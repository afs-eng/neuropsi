type FDTChartSeries = {
  key: string;
  label: string;
  color: string;
  values: number[];
};

type FDTChartData = {
  title: string;
  categories: string[];
  series: FDTChartSeries[];
};

type FDTChartProps = {
  data: FDTChartData | null | undefined;
};

const CHART = {
  width: 900,
  height: 420,
  marginTop: 52,
  marginRight: 40,
  marginBottom: 72,
  marginLeft: 270,
  tickStep: 10,
  legendItemWidth: 145,
};

function getMaxValue(series: FDTChartSeries[]) {
  const values = series.flatMap((item) => item.values || []);
  const rawMax = Math.max(80, ...values, 0);
  return Math.ceil(rawMax / CHART.tickStep) * CHART.tickStep;
}

function getOffsets(size: number) {
  return Array.from({ length: size }, (_, index) => index - (size - 1) / 2);
}

export function FDTChart({ data }: FDTChartProps) {
  if (!data?.categories?.length || !data?.series?.length) return null;

  const maxValue = getMaxValue(data.series);
  const plotWidth = CHART.width - CHART.marginLeft - CHART.marginRight;
  const plotHeight = CHART.height - CHART.marginTop - CHART.marginBottom;
  const rowHeight = plotHeight / data.categories.length;
  const barHeight = Math.min(data.series.length > 2 ? 18 : 28, rowHeight / Math.max(data.series.length, 1));
  const offsets = getOffsets(data.series.length);
  const ticks = Array.from({ length: maxValue / CHART.tickStep + 1 }, (_, index) => index * CHART.tickStep);

  const xScale = (value: number) => CHART.marginLeft + (Math.max(value, 0) / maxValue) * plotWidth;
  const yCenter = (index: number) => CHART.marginTop + rowHeight * index + rowHeight / 2;

  return (
    <div className="overflow-x-auto rounded-[28px] bg-[#eeeeee] p-5 shadow-lg ring-1 ring-black/5 report-print-break-avoid">
      <svg viewBox={`0 0 ${CHART.width} ${CHART.height}`} className="h-auto min-w-[820px] w-full print:min-w-0">
        <text
          x={CHART.width / 2}
          y={28}
          textAnchor="middle"
          style={{ fontFamily: '"Times New Roman", "Liberation Serif", serif', fontSize: 28, fill: '#5f8f3a' }}
        >
          {data.title}
        </text>

        {ticks.map((tick) => {
          const x = xScale(tick);
          return (
            <g key={tick}>
              <line x1={x} x2={x} y1={CHART.marginTop} y2={CHART.height - CHART.marginBottom} stroke="#c9c9c9" strokeWidth="1" />
              <text
                x={x}
                y={CHART.height - CHART.marginBottom + 24}
                textAnchor="middle"
                style={{ fontFamily: '"Times New Roman", "Liberation Serif", serif', fontSize: 11, fill: '#555555' }}
              >
                {tick}
              </text>
            </g>
          );
        })}

        {data.categories.map((category, categoryIndex) => (
          <text
            key={category}
            x={CHART.marginLeft - 14}
            y={yCenter(categoryIndex) + 5}
            textAnchor="end"
            style={{ fontFamily: '"Times New Roman", "Liberation Serif", serif', fontSize: 16, fill: '#555555' }}
          >
            {category}
          </text>
        ))}

        {data.series.map((series, seriesIndex) => (
          <g key={series.key}>
            {series.values.map((value, categoryIndex) => {
              const centerY = yCenter(categoryIndex) + offsets[seriesIndex] * barHeight;
              return (
                <rect
                  key={`${series.key}-${categoryIndex}`}
                  x={CHART.marginLeft}
                  y={centerY - barHeight / 2}
                  width={Math.max(xScale(value) - CHART.marginLeft, 0)}
                  height={barHeight}
                  rx="2"
                  fill={series.color}
                />
              );
            })}
          </g>
        ))}

        {data.series.map((series, index) => {
          const x = CHART.width / 2 - ((data.series.length - 1) * CHART.legendItemWidth) / 2 + index * CHART.legendItemWidth;
          const y = CHART.height - 26;

          return (
            <g key={`legend-${series.key}`}>
              <rect x={x} y={y - 10} width="12" height="12" rx="2" fill={series.color} />
              <text
                x={x + 18}
                y={y}
                style={{ fontFamily: '"Times New Roman", "Liberation Serif", serif', fontSize: 12, fill: '#666666' }}
              >
                {series.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
