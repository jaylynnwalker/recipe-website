import asyncio
from datetime import timedelta
from html.parser import HTMLParser
import ipaddress
import json
import html as html_module
import re
import socket
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree

import httpx

from .ingredient_parser import capitalize_first_letter, normalize_imported_draft, parse_imported_ingredient


class ImportFailure(Exception):
    pass


class YouTubeTranscriptFailure(ImportFailure):
    """A user-facing, non-fatal caption retrieval state."""

    def __init__(self, message: str, reason: str):
        super().__init__(message)
        self.reason = reason


class MetadataParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.json_ld: list[str] = []
        self.metadata: dict[str, str] = {}
        self._script = False
        self._buffer: list[str] = []
        self.images: list[dict[str, str]] = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == 'script' and values.get('type', '').casefold() == 'application/ld+json':
            self._script = True; self._buffer = []
        if tag == 'meta':
            key = values.get('property') or values.get('name')
            if key and values.get('content'): self.metadata[key.casefold()] = values['content']
        if tag == 'img' and (values.get('src') or values.get('data-src')):
            self.images.append(values)

    def handle_data(self, data):
        if self._script: self._buffer.append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self._script:
            self.json_ld.append(''.join(self._buffer)); self._script = False


def validate_external_url(value: str) -> str:
    try: parsed = urlparse(value.strip())
    except ValueError as error: raise ImportFailure('Invalid URL') from error
    if parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.username or parsed.password:
        raise ImportFailure('Only public HTTP or HTTPS URLs are supported')
    try: port = parsed.port
    except ValueError as error: raise ImportFailure('Invalid URL port') from error
    if port not in {None, 80, 443}:
        raise ImportFailure('Non-standard URL ports are not supported')
    try:
        address = ipaddress.ip_address(parsed.hostname)
        if not address.is_global: raise ImportFailure('Private or local network addresses are not allowed')
    except ValueError:
        if parsed.hostname.casefold() in {'localhost', 'localhost.localdomain'} or parsed.hostname.casefold().endswith('.local'):
            raise ImportFailure('Private or local network addresses are not allowed')
    return parsed.geturl()


async def ensure_public_dns(url: str):
    host = urlparse(url).hostname
    try: records = await asyncio.to_thread(socket.getaddrinfo, host, None, type=socket.SOCK_STREAM)
    except socket.gaierror as error: raise ImportFailure('The recipe website could not be resolved') from error
    try: unsafe = not records or any(not ipaddress.ip_address(record[4][0].split('%')[0]).is_global for record in records)
    except ValueError: unsafe = True
    if unsafe:
        raise ImportFailure('The recipe URL resolves to a private or unsafe address')


async def fetch_public_html(url: str) -> tuple[str, str]:
    current = validate_external_url(url)
    async with httpx.AsyncClient(timeout=12, headers={'User-Agent': 'OurKitchenRecipeImporter/1.0', 'Accept': 'text/html,application/xhtml+xml'}) as client:
        for _ in range(4):
            await ensure_public_dns(current)
            try:
                request = client.build_request('GET', current)
                response = await client.send(request, stream=True, follow_redirects=False)
            except httpx.HTTPError as error: raise ImportFailure('The recipe website could not be reached') from error
            try:
                if response.status_code in {301, 302, 303, 307, 308}:
                    location = response.headers.get('location')
                    if not location: raise ImportFailure('The recipe website returned an invalid redirect')
                    current = validate_external_url(urljoin(current, location)); continue
                if response.status_code >= 400: raise ImportFailure(f'The recipe website returned HTTP {response.status_code}')
                content_type = response.headers.get('content-type', '').casefold()
                if 'text/html' not in content_type and 'application/xhtml+xml' not in content_type:
                    raise ImportFailure('The URL did not return an HTML page')
                content = bytearray()
                async for chunk in response.aiter_bytes():
                    content.extend(chunk)
                    if len(content) > 3_000_000: raise ImportFailure('The recipe page is too large to import safely')
                return content.decode(response.encoding or 'utf-8', errors='replace'), current
            finally:
                await response.aclose()
    raise ImportFailure('The recipe website redirected too many times')


def youtube_caption_tracks(html: str) -> list[dict]:
    """Read caption track metadata embedded in YouTube's public player page."""
    match = re.search(r'"captionTracks"\s*:\s*(\[.*?\])\s*,\s*"audioTracks"', html)
    if not match:
        match = re.search(r'"captionTracks"\s*:\s*(\[.*?\])', html)
    if not match: return []
    try:
        tracks = json.loads(match.group(1))
    except (json.JSONDecodeError, TypeError):
        return []
    return [track for track in tracks if isinstance(track, dict) and track.get('baseUrl')]


def select_youtube_caption_track(tracks: list[dict]) -> dict | None:
    if not tracks: return None
    def score(track: dict) -> tuple[int, int]:
        english = str(track.get('languageCode') or '').casefold().startswith('en')
        manual = track.get('kind') != 'asr'
        return (4 if english and manual else 3 if english else 2 if manual else 1, -tracks.index(track))
    return max(tracks, key=score)


def parse_youtube_transcript(content: str) -> str:
    """Flatten YouTube JSON3 or legacy XML captions in chronological order."""
    pieces: list[str] = []
    try:
        payload = json.loads(content)
        for event in payload.get('events', []):
            text = ''.join(str(segment.get('utf8') or '') for segment in event.get('segs', []))
            if text.strip(): pieces.append(text)
    except (json.JSONDecodeError, AttributeError):
        try:
            root = ElementTree.fromstring(content)
            pieces = [''.join(node.itertext()) for node in root.findall('.//text')]
        except ElementTree.ParseError:
            return ''
    return re.sub(r'\s+', ' ', html_module.unescape(' '.join(pieces))).strip()


def clean_pasted_youtube_transcript(content: str) -> str:
    """Remove YouTube page chrome from a transcript copied from the page.

    A clean transcript is returned unchanged apart from surrounding whitespace.
    For a full-page copy, ``Search transcript`` is the stable boundary immediately
    before the caption text. Timestamp-only display lines are redundant because
    the spoken lines remain in chronological order.
    """
    lines = content.strip().splitlines()
    boundaries = [index for index, line in enumerate(lines) if line.strip().casefold() == 'search transcript']
    if boundaries:
        lines = lines[boundaries[-1] + 1:]
    timestamp = re.compile(r'^\d{1,2}:\d{2}(?::\d{2})?$')
    spoken_time = re.compile(r'^\d+\s+(?:(?:hours?|minutes?),?\s*)?(?:\d+\s+)?seconds?$' , re.IGNORECASE)
    cleaned = [line.strip() for line in lines if line.strip() and not timestamp.fullmatch(line.strip()) and not spoken_time.fullmatch(line.strip())]
    return '\n'.join(cleaned).strip()


async def fetch_youtube_transcript(html: str) -> tuple[str, str]:
    """Fetch a public manual or automatic caption track without downloading video."""
    track = select_youtube_caption_track(youtube_caption_tracks(html))
    if not track:
        raise YouTubeTranscriptFailure('No public YouTube transcript is available. Paste transcript text below or complete the recipe manually.', 'unavailable')
    caption_url = str(track['baseUrl'])
    separator = '&' if '?' in caption_url else '?'
    caption_url = f'{caption_url}{separator}fmt=json3'
    current = validate_external_url(caption_url)
    try:
        async with httpx.AsyncClient(timeout=12, headers={'User-Agent': 'OurKitchenRecipeImporter/1.0', 'Accept': 'application/json,text/xml,application/xml,text/plain'}) as client:
            for _ in range(4):
                await ensure_public_dns(current)
                response = await client.get(current, follow_redirects=False)
                if response.status_code in {301, 302, 303, 307, 308}:
                    location = response.headers.get('location')
                    if not location: raise YouTubeTranscriptFailure('YouTube returned an invalid transcript redirect.', 'failed')
                    current = validate_external_url(urljoin(current, location)); continue
                if response.status_code in {403, 429}:
                    raise YouTubeTranscriptFailure('YouTube transcript retrieval was blocked. Retry later or paste transcript text below.', 'blocked')
                if response.status_code >= 400:
                    raise YouTubeTranscriptFailure(f'YouTube transcript retrieval failed with HTTP {response.status_code}. Retry or paste transcript text below.', 'failed')
                if len(response.content) > 2_000_000:
                    raise YouTubeTranscriptFailure('The YouTube transcript is too large to process safely.', 'failed')
                transcript = parse_youtube_transcript(response.text)
                if not transcript:
                    raise YouTubeTranscriptFailure('The YouTube transcript was retrieved but contained no usable text. Paste transcript text below or complete the recipe manually.', 'insufficient')
                language = str(track.get('languageCode') or 'unknown')
                kind = 'automatic captions' if track.get('kind') == 'asr' else 'manual captions'
                return transcript, f'{language} {kind}'
    except YouTubeTranscriptFailure:
        raise
    except (httpx.HTTPError, ImportFailure) as error:
        raise YouTubeTranscriptFailure('YouTube transcript retrieval failed. Retry later or paste transcript text below.', 'failed') from error
    raise YouTubeTranscriptFailure('YouTube transcript retrieval redirected too many times.', 'failed')


def duration_minutes(value) -> int:
    if not isinstance(value, str): return 0
    match = re.fullmatch(r'P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?', value)
    if not match: return 0
    days, hours, minutes, seconds = (int(part or 0) for part in match.groups())
    return int(timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds).total_seconds() // 60)


def nodes(value):
    if isinstance(value, list):
        for item in value: yield from nodes(item)
    elif isinstance(value, dict):
        yield value
        if '@graph' in value: yield from nodes(value['@graph'])


def type_is(node: dict, kind: str) -> bool:
    kinds = node.get('@type', [])
    return kind in ([kinds] if isinstance(kinds, str) else kinds)


def instruction_text(value) -> list[str]:
    result = []
    for item in value if isinstance(value, list) else [value]:
        if isinstance(item, str) and item.strip(): result.append(item.strip())
        elif isinstance(item, dict):
            if item.get('text'): result.append(str(item['text']).strip())
            elif item.get('itemListElement'): result.extend(instruction_text(item['itemListElement']))
    return result


def sectioned_instructions(value) -> tuple[list[dict], list[dict]]:
    sections: list[dict] = []; steps: list[dict] = []
    for item in value if isinstance(value, list) else [value]:
        if isinstance(item, dict) and type_is(item, 'HowToSection'):
            heading = str(item.get('name') or '').strip()
            if not heading: continue
            section_index = len(sections); sections.append({'heading': heading})
            for text in instruction_text(item.get('itemListElement', [])):
                steps.append({'instruction': capitalize_first_letter(text), 'tip': None, 'section_index': section_index})
        else:
            for text in instruction_text(item):
                steps.append({'instruction': capitalize_first_letter(text), 'tip': None, 'section_index': None})
    return sections, steps


def sectioned_ingredients(values) -> tuple[list[dict], list[dict]]:
    sections: list[dict] = []; ingredients: list[dict] = []; section_index = None
    for raw in values if isinstance(values, list) else [values]:
        text = str(raw).strip()
        is_heading = text.endswith(':') and len(text) <= 80 and not re.search(r'\d', text)
        if is_heading:
            heading = text[:-1].strip()
            if heading:
                section_index = len(sections); sections.append({'heading': heading})
            continue
        if text:
            ingredients.append({**parse_imported_ingredient(text), 'section_index': section_index})
    return sections, ingredients


def _image_value(value) -> str | None:
    if isinstance(value, str): return value.strip() or None
    if isinstance(value, list):
        return next((result for item in value if (result := _image_value(item))), None)
    if isinstance(value, dict):
        return _image_value(value.get('url') or value.get('contentUrl'))
    return None


def image_url_from_page(html: str, final_url: str) -> str | None:
    """Choose a likely finished-dish image without fetching it."""
    parser = MetadataParser(); parser.feed(html)
    decoded = []
    for raw in parser.json_ld:
        try: decoded.append(json.loads(raw))
        except (json.JSONDecodeError, TypeError): continue
    recipe = next((node for value in decoded for node in nodes(value) if type_is(node, 'Recipe')), None)
    candidates = [
        _image_value(recipe.get('image')) if recipe else None,
        parser.metadata.get('og:image:secure_url'), parser.metadata.get('og:image'),
        parser.metadata.get('twitter:image'), parser.metadata.get('twitter:image:src'),
    ]
    selected = next((candidate for candidate in candidates if candidate), None)
    if not selected:
        scored = []
        for image in parser.images:
            source = image.get('src') or image.get('data-src') or ''
            context = ' '.join([source, image.get('alt', ''), image.get('class', ''), image.get('id', '')]).casefold()
            if any(word in context for word in ('logo', 'avatar', 'icon', 'banner', 'advert', 'tracking', 'pixel')): continue
            score = sum(word in context for word in ('recipe', 'dish', 'food', 'hero', 'main', 'featured'))
            try: score += int(image.get('width', '0')) >= 500
            except ValueError: pass
            scored.append((score, source))
        if scored: selected = max(scored, key=lambda item: item[0])[1]
    if not selected: return None
    try: return validate_external_url(urljoin(final_url, selected))
    except ImportFailure: return None


def public_text_from_html(html: str) -> str:
    cleaned = re.sub(r'<(script|style)\b[^>]*>.*?</\1>', ' ', html, flags=re.IGNORECASE | re.DOTALL)
    return re.sub(r'\s+', ' ', html_module.unescape(re.sub(r'<[^>]+>', ' ', cleaned))).strip()


def clean_social_title(value: str) -> str:
    title = re.sub(r'^\s*[\d.,]+\s*[KMB]?\s+(?:views?|reactions?|likes?)\s*(?:[·|]\s*)?', '', value, flags=re.IGNORECASE)
    title = re.sub(r'^\s*[\d.,]+\s*[KMB]?\s+(?:views?|reactions?|likes?)\s*(?:[·|]\s*)?', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*#[\w-]+', '', title)
    parts = [part.strip() for part in title.split('|') if part.strip()]
    return (parts[0] if parts else title).strip(' -·')


def parse_page(html: str, final_url: str) -> tuple[dict, bool]:
    parser = MetadataParser(); parser.feed(html)
    decoded = []
    for raw in parser.json_ld:
        try: decoded.append(json.loads(raw))
        except (json.JSONDecodeError, TypeError): continue
    recipe = next((node for value in decoded for node in nodes(value) if type_is(node, 'Recipe')), None)
    host = urlparse(final_url).hostname or 'Recipe website'
    if recipe:
        raw_ingredients = recipe.get('recipeIngredient', [])
        if isinstance(raw_ingredients, str): raw_ingredients = [raw_ingredients]
        ingredients = [str(item).strip() for item in raw_ingredients if str(item).strip()]
        ingredient_sections, parsed_ingredients = sectioned_ingredients(ingredients)
        instruction_sections, parsed_steps = sectioned_instructions(recipe.get('recipeInstructions', []))
        steps = [step['instruction'] for step in parsed_steps]
        raw_yield = recipe.get('recipeYield', '')
        if isinstance(raw_yield, list): raw_yield = next((value for value in raw_yield if re.search(r'\d+', str(value))), raw_yield[0] if raw_yield else '')
        servings_match = re.search(r'\d+', str(raw_yield))
        yield_unit = re.sub(r'^.*?\d+(?:\.\d+)?\s*', '', str(raw_yield)).strip() or 'servings'
        prep_minutes = duration_minutes(recipe.get('prepTime'))
        cook_minutes = duration_minutes(recipe.get('cookTime'))
        total_minutes = duration_minutes(recipe.get('totalTime'))
        additional_minutes = max(0, total_minutes - prep_minutes - cook_minutes) if total_minutes else 0
        extracted_title = str(recipe.get('name') or parser.metadata.get('og:title') or parser.metadata.get('twitter:title') or '').strip()
        title = extracted_title or 'Recipe title needed'
        cuisine = recipe.get('recipeCuisine') or ''
        if isinstance(cuisine, list): cuisine = ', '.join(str(value) for value in cuisine)
        raw_categories = recipe.get('recipeCategory') or []
        if isinstance(raw_categories, str): raw_categories = [item.strip() for item in raw_categories.split(',')]
        raw_keywords = recipe.get('keywords') or []
        if isinstance(raw_keywords, str): raw_keywords = [item.strip() for item in raw_keywords.split(',')]
        draft = {
            'title': title, 'description': str(recipe.get('description') or '').strip(), 'status': 'Want to Try', 'cuisine': str(cuisine).strip(), 'proteins': [],
            'tags': [str(item).strip() for item in raw_keywords if str(item).strip()], 'categories': [str(item).strip() for item in raw_categories if str(item).strip()], 'prep_minutes': prep_minutes, 'cook_minutes': cook_minutes, 'additional_time_minutes': additional_minutes, 'additional_time_label': 'Additional', 'base_servings': int(servings_match.group()) if servings_match else None, 'yield_unit': yield_unit if servings_match else '',
            'ingredient_sections': ingredient_sections, 'instruction_sections': instruction_sections,
            'ingredients': parsed_ingredients,
            'steps': parsed_steps, 'notes': '',
            'source': {'type': 'web', 'label': host, 'url': final_url, 'page': None},
        }
        return normalize_imported_draft(draft), bool(extracted_title and ingredients and steps)
    source_type = social_source_type(host)
    if source_type:
        video = next((node for value in decoded for node in nodes(value) if type_is(node, 'VideoObject')), {})
        label = {'youtube': 'YouTube', 'instagram': 'Instagram', 'facebook': 'Facebook'}[source_type]
        raw_title = str(video.get('name') or parser.metadata.get('og:title') or parser.metadata.get('twitter:title') or '').strip()
        title = clean_social_title(raw_title) or f'{label} recipe — title needed'
        description = str(video.get('description') or parser.metadata.get('og:description') or parser.metadata.get('description') or '').strip()
        return empty_draft(title, description, final_url, source_type, host), False
    raise ImportFailure('No structured recipe metadata was found. You can retry or add this recipe manually.')


def empty_draft(title: str, description: str, url: str | None, source_type: str, label: str) -> dict:
    return {'title': title, 'description': description, 'status': 'Want to Try', 'cuisine': '', 'proteins': [], 'tags': [], 'categories': [], 'ingredient_sections': [], 'instruction_sections': [], 'prep_minutes': 0, 'cook_minutes': 0, 'additional_time_minutes': 0, 'additional_time_label': 'Additional', 'base_servings': None, 'yield_unit': '', 'ingredients': [], 'steps': [], 'notes': '', 'source': {'type': source_type, 'label': label, 'url': url, 'page': None}}


async def extract_url(url: str) -> tuple[dict, bool, str, str | None]:
    html, final_url = await fetch_public_html(url)
    draft, complete = parse_page(html, final_url)
    return draft, complete, final_url, image_url_from_page(html, final_url)


def social_source_type(host: str) -> str | None:
    normalized = host.casefold().removeprefix('www.').removeprefix('m.')
    if normalized in {'youtu.be', 'youtube.com', 'youtube-nocookie.com'}: return 'youtube'
    if normalized in {'instagram.com', 'instagr.am'}: return 'instagram'
    if normalized in {'facebook.com', 'fb.watch'}: return 'facebook'
    return None
