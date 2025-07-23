'use client';

import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Area,
  AreaChart,
} from 'recharts';
import { ChartContainer } from './chart-container';

interface DataPoint {
  [key: string]: string | number;
}

interface LineChartComponentProps {
  title: string;
  description?: string;
  data: DataPoint[];
  dataKeys: {
    key: string;
    name: string;
    color: string;
  }[];
  xAxisKey: string;
  height?: number;
  isLoading?: boolean;
  error?: Error | null;
  showArea?: boolean;
  showGrid?: boolean;
  showLegend?: boolean;
  formatXAxis?: (value: any) => string;
  formatYAxis?: (value: any) => string;
  formatTooltip?: (value: any, name: string) => [string, string];
}

export function LineChartComponent({
  title,
  description,
  data,
  dataKeys,
  xAxisKey,
  height = 300,
  isLoading = false,
  error = null,
  showArea = false,
  showGrid = true,
  showLegend = true,
  formatXAxis,
  formatYAxis,
  formatTooltip,
}: LineChartComponentProps) {
  const Chart = showArea ? AreaChart : LineChart;

  return (
    <ChartContainer title={title} description={description} isLoading={isLoading} error={error}>
      <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <Chart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />}
            <XAxis
              dataKey={xAxisKey}
              tickFormatter={formatXAxis}
              className="text-xs"
              tick={{ fontSize: 12 }}
            />
            <YAxis tickFormatter={formatYAxis} className="text-xs" tick={{ fontSize: 12 }} />
            <Tooltip
              contentStyle={{
                backgroundColor: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '8px',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
              }}
              formatter={formatTooltip}
              labelStyle={{ color: 'hsl(var(--foreground))' }}
            />
            {showLegend && <Legend wrapperStyle={{ paddingTop: '20px' }} />}
            {dataKeys.map((item) =>
              showArea ? (
                <Area
                  key={item.key}
                  type="monotone"
                  dataKey={item.key}
                  stroke={item.color}
                  fill={item.color}
                  fillOpacity={0.3}
                  strokeWidth={2}
                  name={item.name}
                  dot={{ fill: item.color, strokeWidth: 0, r: 4 }}
                  activeDot={{ r: 6, stroke: item.color, strokeWidth: 2 }}
                />
              ) : (
                <Line
                  key={item.key}
                  type="monotone"
                  dataKey={item.key}
                  stroke={item.color}
                  strokeWidth={2}
                  name={item.name}
                  dot={{ fill: item.color, strokeWidth: 0, r: 4 }}
                  activeDot={{ r: 6, stroke: item.color, strokeWidth: 2 }}
                />
              )
            )}
          </Chart>
        </ResponsiveContainer>
      </div>
    </ChartContainer>
  );
}

// Specialized productivity trends chart
export function ProductivityTrendsChart({
  data,
  isLoading,
  error,
}: {
  data: Array<{
    period_start: string;
    tasks_created: number;
    tasks_completed: number;
    hours_logged: number;
  }>;
  isLoading?: boolean;
  error?: Error | null;
}) {
  const chartData = data.map((item) => ({
    period: new Date(item.period_start).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    }),
    created: item.tasks_created,
    completed: item.tasks_completed,
    hours: item.hours_logged,
  }));

  return (
    <LineChartComponent
      title="Productivity Trends"
      description="Tasks created, completed, and hours logged over time"
      data={chartData}
      dataKeys={[
        { key: 'created', name: 'Tasks Created', color: '#3b82f6' },
        { key: 'completed', name: 'Tasks Completed', color: '#10b981' },
        { key: 'hours', name: 'Hours Logged', color: '#f59e0b' },
      ]}
      xAxisKey="period"
      height={350}
      isLoading={isLoading}
      error={error}
      showArea={true}
      formatTooltip={(value, name) => [
        name === 'Hours Logged' ? `${value}h` : value.toString(),
        name,
      ]}
    />
  );
}
