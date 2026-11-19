# Maths notation in study content

## M6 decision

Keep equations in the version 1 content bundle as plain, selectable text. Each quantitative solution step contains a short Turkish heading and a single operation. Use a decimal comma, spaces around operators, the multiplication sign (×), and parentheses to group the numerator or denominator of a fraction written with a slash. Preserve imported line breaks. The shared React Native Text component wraps the lines inside the available reading column on web, iOS and Android. [React Native Text](https://reactnative.dev/docs/text)

## Spike

The existing percentage problem in the offline seed includes the ratio `(0,4 × N + 5) / (N + 5) = 0,5`. The reader displays each transformation separately and finishes with `N = 2,5 / 0,1 = 25`. The component test compares the displayed operation strings with the imported steps. Playwright answers the same question through the study library, finds the final equation, and checks the page width for overflow at 390 and 1280 px. [Seed problem](../content/seed/sample-content.json) · [Component test](../apps/app/tests/study.test.tsx) · [Browser test](../apps/app/e2e/study.spec.ts)

Stacked fractions, matrices, or notation that relies on vertical alignment would justify another trial using actual examples from a future content batch. A TeX renderer such as KaTeX produces HTML and MathML, so a native implementation would need a rendering surface and accessibility checks on both phone platforms. The current corpus and the existing shared text component require no additional package. [KaTeX output options](https://katex.org/docs/options)
