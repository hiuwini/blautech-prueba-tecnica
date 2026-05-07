import {
  DOCUMENT_STATUS_LABELS,
  DOCUMENT_STATUSES,
} from "../../documents/model/statuses";
import type { DocumentStatus } from "../../documents/model/types";

export function StatusBarChart({
  counts,
}: {
  counts: Record<DocumentStatus, number>;
}) {
  const entries = DOCUMENT_STATUSES.map((status) => ({
    status,
    label: DOCUMENT_STATUS_LABELS[status],
    value: counts[status] ?? 0,
  }));
  const total = entries.reduce((sum, entry) => sum + entry.value, 0);
  const maxValue = Math.max(1, ...entries.map((entry) => entry.value));

  const width = 320;
  const height = 120;
  const paddingX = 16;
  const paddingTop = 12;
  const paddingBottom = 22;
  const innerWidth = width - paddingX * 2;
  const innerHeight = height - paddingTop - paddingBottom;
  const slot = innerWidth / entries.length;
  const barWidth = Math.max(8, slot - 10);

  return (
    <figure
      className="status-chart"
      role="img"
      aria-label={`Distribucion por estado, total ${total}`}
      data-testid="status-chart"
    >
      <figcaption className="status-chart-caption">Por estado</figcaption>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="xMidYMid meet"
        focusable="false"
        aria-hidden="true"
      >
        <line
          x1={paddingX}
          x2={width - paddingX}
          y1={height - paddingBottom}
          y2={height - paddingBottom}
          className="status-chart-axis"
        />
        {entries.map((entry, index) => {
          const barHeight =
            entry.value === 0
              ? 0
              : Math.max(2, (entry.value / maxValue) * innerHeight);
          const x = paddingX + slot * index + (slot - barWidth) / 2;
          const y = height - paddingBottom - barHeight;
          return (
            <g
              key={entry.status}
              data-testid={`status-chart-bar-${entry.status.toLowerCase()}`}
            >
              <rect
                x={x}
                y={y}
                width={barWidth}
                height={barHeight}
                rx={3}
                className={`status-chart-bar status-chart-${entry.status.toLowerCase()}`}
              >
                <title>{`${entry.label}: ${entry.value}`}</title>
              </rect>
              {entry.value > 0 ? (
                <text
                  x={x + barWidth / 2}
                  y={y - 4}
                  textAnchor="middle"
                  className="status-chart-value"
                >
                  {entry.value}
                </text>
              ) : null}
              <text
                x={x + barWidth / 2}
                y={height - 6}
                textAnchor="middle"
                className="status-chart-label"
              >
                {entry.label}
              </text>
            </g>
          );
        })}
      </svg>
    </figure>
  );
}
