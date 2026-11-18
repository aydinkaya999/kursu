import { tr } from "../i18n/tr";
const numberFormat = new Intl.NumberFormat("tr-TR", {
  maximumFractionDigits: 10,
});
const currencyFormat = new Intl.NumberFormat("tr-TR", {
  style: "currency",
  currency: "TRY",
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
});
export const formatNumber = (value: number) => numberFormat.format(value);
export const formatCurrency = (value: number) => currencyFormat.format(value);
export const formatPercent = (value: number) => "%" + formatNumber(value);
export const formatRange = (low: number, high: number) =>
  formatNumber(low) + "–" + formatNumber(high);
export const formatDuration = (minutes: number) =>
  formatNumber(minutes) + " " + tr.controls.durationUnit;
export function formatTimer(seconds: number) {
  const total = Math.max(0, Math.floor(seconds));
  return (
    String(Math.floor(total / 60)).padStart(2, "0") +
    ":" +
    String(total % 60).padStart(2, "0")
  );
}
const dateOptions = {
  timeZone: "Europe/Istanbul",
  day: "numeric",
  month: "long",
} as const;
const dayMonth = new Intl.DateTimeFormat("tr-TR", dateOptions);
const weekday = new Intl.DateTimeFormat("tr-TR", {
  timeZone: dateOptions.timeZone,
  weekday: "long",
});
const fullDate = new Intl.DateTimeFormat("tr-TR", {
  ...dateOptions,
  year: "numeric",
});
export function formatDate(
  value: Date | string,
  kind: "weekday" | "year" = "year",
) {
  const date = typeof value === "string" ? new Date(value) : value;
  return kind === "year"
    ? fullDate.format(date)
    : dayMonth.format(date) + " " + weekday.format(date);
}
const units = [
  "sıfır",
  "bir",
  "iki",
  "üç",
  "dört",
  "beş",
  "altı",
  "yedi",
  "sekiz",
  "dokuz",
] as const;
const tens = [
  "",
  "on",
  "yirmi",
  "otuz",
  "kırk",
  "elli",
  "altmış",
  "yetmiş",
  "seksen",
  "doksan",
] as const;
const scales = ["", "bin", "milyon", "milyar", "trilyon", "katrilyon"] as const;
function finalWord(value: number): string {
  if (!Number.isSafeInteger(value))
    throw new RangeError("Expected a safe integer");
  let n = Math.abs(value);
  if (n === 0) return units[0];
  let scale = 0;
  while (n % 1000 === 0) {
    n /= 1000;
    scale++;
  }
  if (scale) return scales[scale]!;
  if (n % 10) return units[n % 10]!;
  if (n % 100) return tens[Math.floor(n / 10) % 10]!;
  return "yüz";
}
export function numberSuffix(
  value: number,
  form: "possessive" | "accusative" = "possessive",
): string {
  const word = finalWord(value);
  const vowels = word.match(/[aeıioöuü]/g)!;
  const last = vowels[vowels.length - 1]!;
  const vowel = "aı".includes(last)
    ? "ı"
    : "ei".includes(last)
      ? "i"
      : "ou".includes(last)
        ? "u"
        : "ü";
  const ending = (/[aeıioöuü]$/.test(word) ? "s" : "") + vowel;
  return "'" + ending + (form === "accusative" ? "n" + vowel : "");
}
export const inflectedNumber = (
  value: number,
  form: "possessive" | "accusative" = "possessive",
) => formatNumber(value) + numberSuffix(value, form);
