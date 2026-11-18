import { StyleSheet, View } from "react-native";
import { colors, line, space } from "../theme";
import { Label } from "./Core";
import type { DataTableProps } from "./DataTable.types";

export function DataTable({
  label,
  headers,
  rows,
  highlightedColumn,
}: DataTableProps) {
  return (
    <View accessibilityLabel={label}>
      {[headers, ...rows].map((cells, row) => (
        <View
          key={row}
          accessible
          accessibilityLabel={
            row === 0
              ? cells.join(", ")
              : cells
                  .map((value, column) =>
                    column === 0 ? value : headers[column] + " " + value,
                  )
                  .join(", ")
          }
          style={[styles.row, row > 0 && styles.divider]}
        >
          {cells.map((value, column) => {
            const highlight = column === highlightedColumn;
            return (
              <View
                key={column}
                style={[
                  styles.cell,
                  column === 0 && styles.first,
                  highlight && styles.highlight,
                ]}
              >
                <Label
                  variant={row === 0 ? "caption" : "table"}
                  weight={row === 0 ? 700 : highlight ? 800 : 600}
                  color={
                    highlight
                      ? colors.primaryStrong
                      : row === 0
                        ? colors.inkMuted
                        : colors.ink
                  }
                  figures={row > 0 && column > 0}
                  style={column > 0 && styles.numeric}
                >
                  {value}
                </Label>
              </View>
            );
          })}
        </View>
      ))}
    </View>
  );
}
const styles = StyleSheet.create({
  row: { flexDirection: "row" },
  divider: { borderTopWidth: line.hair, borderColor: colors.line },
  cell: {
    flex: 1,
    paddingVertical: space.x8,
    paddingHorizontal: space.x6,
    justifyContent: "center",
  },
  first: { flex: 2 },
  highlight: { backgroundColor: colors.primaryTint },
  numeric: { textAlign: "right" },
});
