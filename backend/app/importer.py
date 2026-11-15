import asyncio
from datetime import timedelta
from html.parser import HTMLParser
import ipaddress
import json
import re
import socket
from urllib.parse import urljoin, urlparse

import httpx


class ImportFailure(Exception):
    pass


class MetadataParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.json_ld: list[str] = []
        self.metadata: dict[str, str] = {}
        self._script = False
        self._buffer: list[str] = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == 'script' and values.get('type', '').casefold() == 'application/ld+json':
            self._script = True; self._buffer = []
        if tag == 'meta':
            key = values.get('property') or values.get('name')
            if key and values.get('content'): self.metadata[key.casefold()] = values['content']

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
        steps = instruction_text(recipe.get('recipeInstructions', []))
        servings_match = re.search(r'\d+', str(recipe.get('recipeYield', '')))
        title = str(recipe.get('name') or parser.metadata.get('og:title') or host).strip()
        cuisine = recipe.get('recipeCuisine') or ''
        if isinstance(cuisine, list): cuisine = ', '.join(str(value) for value in cuisine)
        return {
            'title': title, 'description': str(recipe.get('description') or '').strip(), 'status': 'Want to Try', 'cuisine': str(cuisine).strip(), 'protein': '',
            'tags': [], 'categories': [], 'prep_minutes': duration_minutes(recipe.get('prepTime')), 'cook_minutes': duration_minutes(recipe.get('cookTime')), 'base_servings': int(servings_match.group()) if servings_match else 4,
            'ingredients': [{'name': item, 'quantity': None, 'unit': None, 'note': None, 'optional': False} for item in ingredients],
            'steps': [{'instruction': item, 'tip': None} for item in steps], 'notes': '',
            'source': {'type': 'web', 'label': host, 'url': final_url, 'page': None},
        }, bool(title and ingredients and steps)
    is_youtube = host.casefold() in {'youtu.be', 'youtube.com', 'www.youtube.com', 'm.youtube.com'}
    if is_youtube:
        video = next((node for value in decoded for node in nodes(value) if type_is(node, 'VideoObject')), {})
        title = str(video.get('name') or parser.metadata.get('og:title') or 'YouTube recipe video').strip()
        description = str(video.get('description') or parser.metadata.get('og:description') or parser.metadata.get('description') or '').strip()
        return empty_draft(title, description, final_url, 'youtube', host), False
    raise ImportFailure('No structured recipe metadata was found. You can retry or add this recipe manually.')


def empty_draft(title: str, description: str, url: str | None, source_type: str, label: str) -> dict:
    return {'title': title, 'description': description, 'status': 'Want to Try', 'cuisine': '', 'protein': '', 'tags': [], 'categories': [], 'prep_minutes': 0, 'cook_minutes': 0, 'base_servings': 4, 'ingredients': [], 'steps': [], 'notes': '', 'source': {'type': source_type, 'label': label, 'url': url, 'page': None}}


async def extract_url(url: str) -> tuple[dict, bool, str]:
    html, final_url = await fetch_public_html(url)
    draft, complete = parse_page(html, final_url)
    return draft, complete, final_url
