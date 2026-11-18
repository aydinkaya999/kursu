import type { CSSProperties } from "react";
import { colors, line, space } from "../theme";
import { useWebTextStyle } from "../theme/webTypography";
import type { DataTableProps } from "./DataTable.types";

export function DataTable({
  label,
  headers,
  rows,
  highlightedColumn,
}: DataTableProps) {
  const head = useWebTextStyle("caption", 700);
  const body = useWebTextStyle("table", 600);
  const emphasis = useWebTextStyle("table", 800);
  function cell(column: number, header: boolean): CSSProperties {
    const highlighted = column === highlightedColumn;
    return {
      ...(header ? head : highlighted ? emphasis : body),
      padding: space.x8 + "px " + space.x6 + "px",
      textAlign: column === 0 ? "left" : "right",
      color: highlighted
        ? colors.primaryStrong
        : header
          ? colors.inkMuted
          : colors.ink,
      backgroundColor: highlighted ? colors.primaryTint : undefined,
      borderTop: header ? undefined : line.hair + "px solid " + colors.line,
      fontVariantNumeric: column > 0 ? "tabular-nums" : undefined,
    };
  }
  return (
    <table
      aria-label={label}
      style={{ width: "100%", borderCollapse: "collapse" }}
    >
      <thead>
        <tr>
          {headers.map((header, column) => (
            <th key={column} scope="col" style={cell(column, true)}>
              {header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, index) => (
          <tr key={index}>
            {row.map((value, column) =>
              column === 0 ? (
                <th key={column} scope="row" style={cell(column, false)}>
                  {value}
                </th>
              ) : (
                <td key={column} style={cell(column, false)}>
                  {value}
                </td>
              ),
            )}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
