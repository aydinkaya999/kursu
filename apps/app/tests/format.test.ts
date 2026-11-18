import {
  formatCurrency,
  formatDate,
  formatDuration,
  formatNumber,
  formatPercent,
  formatRange,
  formatTimer,
  inflectedNumber,
  numberSuffix,
} from "../src/lib/format";

const suffixes = [
  [0, "'ı", "'ını"],
  [1, "'i", "'ini"],
  [2, "'si", "'sini"],
  [3, "'ü", "'ünü"],
  [4, "'ü", "'ünü"],
  [5, "'i", "'ini"],
  [6, "'sı", "'sını"],
  [7, "'si", "'sini"],
  [8, "'i", "'ini"],
  [9, "'u", "'unu"],
  [10, "'u", "'unu"],
  [20, "'si", "'sini"],
  [30, "'u", "'unu"],
  [40, "'ı", "'ını"],
  [50, "'si", "'sini"],
  [60, "'ı", "'ını"],
  [70, "'i", "'ini"],
  [80, "'i", "'ini"],
  [90, "'ı", "'ını"],
  [100, "'ü", "'ünü"],
  [71, "'i", "'ini"],
  [104, "'ü", "'ünü"],
  [250, "'si", "'sini"],
  [900, "'ü", "'ünü"],
  [21000, "'i", "'ini"],
  [2000000, "'u", "'unu"],
  [1000000000, "'ı", "'ını"],
  [1000000000000, "'u", "'unu"],
  [-12, "'si", "'sini"],
] as const;
it.each(suffixes)(
  "inflects %i by its final spoken word",
  (value, possessive, accusative) => {
    expect(numberSuffix(value)).toBe(possessive);
    expect(numberSuffix(value, "accusative")).toBe(accusative);
  },
);
it("rejects fractional and unsafe counts", () => {
  for (const count of [0.1, Infinity, NaN, Number.MAX_SAFE_INTEGER + 1])
    expect(() => numberSuffix(count)).toThrow(RangeError);
});
it("formats the Turkish examples in the design system", () => {
  expect(formatNumber(38.25)).toBe("38,25");
  expect(formatNumber(1420)).toBe("1.420");
  expect(formatPercent(71)).toBe("%71");
  expect(formatCurrency(990)).toBe("₺990");
  expect(formatRange(28, 34)).toBe("28–34");
  expect(formatDuration(10)).toBe("10 dk");
  expect(formatTimer(81 * 60 + 36)).toBe("81:36");
  expect(formatTimer(8)).toBe("00:08");
  expect(formatTimer(-1)).toBe("00:00");
  expect(formatDate("2027-01-31T21:00:00Z", "weekday")).toBe(
    "1 Şubat Pazartesi",
  );
  expect(formatDate("2027-02-06T21:00:00Z", "year")).toBe("7 Şubat 2027");
  expect(inflectedNumber(104, "accusative")).toBe("104'ünü");
  expect(inflectedNumber(1020)).toBe("1.020'si");
});
