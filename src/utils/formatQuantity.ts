const fractions: Record<number, string> = {
  0.125: '⅛',
  0.25: '¼',
  0.333: '⅓',
  0.5: '½',
  0.667: '⅔',
  0.75: '¾',
}

export function formatQuantity(value: number | null, scale = 1): string {
  if (value === null) return ''
  const scaled = value * scale
  const whole = Math.floor(scaled)
  const decimal = scaled - whole
  const key = Object.keys(fractions)
    .map(Number)
    .find((fraction) => Math.abs(decimal - fraction) < 0.02)

  if (key !== undefined) return `${whole || ''}${fractions[key]}`
  return Number.isInteger(scaled) ? String(scaled) : String(Math.round(scaled * 100) / 100)
}
