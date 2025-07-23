'use client';

import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { ChartContainer } from './chart-container';

interface DataPoint {
  name: string;
  value: number;
  color: string;
}

interface DonutChartComponentProps {
  title: string;
  description?: string;
  data: DataPoint[];
  height?: number;
  isLoading?: boolean;
  error?: Error | null;
  showLegend?: boolean;
  showLabels?: boolean;
  innerRadius?: number;
  outerRadius?: number;
  formatTooltip?: (value: any, name: string) => [string, string];
  formatLabel?: (entry: DataPoint) => string;
}

export function DonutChartComponent({
  title,
  description,
  data,
  height = 300,
  isLoading = false,
  error = null,
  showLegend = true,
  showLabels = false,
  innerRadius = 60,
  outerRadius = 120,
  formatTooltip,
  formatLabel,
}: DonutChartComponentProps) {
  const total = data.reduce((sum, item) => sum + item.value, 0);

  const renderLabel = (entry: any) => {
    if (!showLabels) return '';
    if (formatLabel) return formatLabel(entry);
    const percent = ((entry.value / total) * 100).toFixed(1);
    return `${percent}%`;
  };

  const defaultTooltip = (value: any, name: string) => [
    `${value} (${((value / total) * 100).toFixed(1)}%)`,
    name,
  ];

  return (
    <ChartContainer title={title} description={description} isLoading={isLoading} error={error}>
      <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={showLabels ? renderLabel : false}
              outerRadius={outerRadius}
              innerRadius={innerRadius}
              fill="#8884d8"
              dataKey="value"
              stroke="hsl(var(--card))"
              strokeWidth={2}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '8px',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
              }}
              formatter={formatTooltip || defaultTooltip}
              labelStyle={{ color: 'hsl(var(--foreground))' }}
            />
            {showLegend && (
              <Legend
                verticalAlign="bottom"
                height={36}
                iconType="circle"
                wrapperStyle={{
                  paddingTop: '20px',
                  fontSize: '12px',
                }}
              />
            )}
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Center content for total */}
      {innerRadius > 0 && (
        <div
          className="absolute inset-0 flex items-center justify-center pointer-events-none"
          style={{
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            marginTop: '-20px', // Adjust for card header
          }}
        >
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">{total}</div>
            <div className="text-xs text-muted-foreground">Total</div>
          </div>
        </div>
      )}
    </ChartContainer>
  );
}

// Specialized task status distribution chart
export function TaskStatusChart({
  data,
  isLoading,
  error,
}: {
  data: Record<string, number>;
  isLoading?: boolean;
  error?: Error | null;
}) {
  const statusColors: Record<string, string> = {
    todo: '#6b7280',
    'in-progress': '#f59e0b',
    completed: '#10b981',
    'on-hold': '#ef4444',
    cancelled: '#8b5cf6',
  };

  const chartData = Object.entries(data)
    .map(([status, count]) => ({
      name: status.replace('-', ' ').replace(/\b\w/g, (l) => l.toUpperCase()),
      value: count,
      color: statusColors[status] || '#6b7280',
    }))
    .filter((item) => item.value > 0);

  return (
    <DonutChartComponent
      title="Task Status Distribution"
      description="Breakdown of tasks by current status"
      data={chartData}
      height={350}
      isLoading={isLoading}
      error={error}
      formatTooltip={(value, name) => [`${value} tasks`, name]}
    />
  );
}

// Specialized task priority distribution chart
export function TaskPriorityChart({
  data,
  isLoading,
  error,
}: {
  data: Record<string, number>;
  isLoading?: boolean;
  error?: Error | null;
}) {
  const priorityColors: Record<string, string> = {
    low: '#10b981',
    medium: '#f59e0b',
    high: '#ef4444',
    urgent: '#dc2626',
  };

  const priorityOrder = ['low', 'medium', 'high', 'urgent'];

  const chartData = priorityOrder
    .filter((priority) => data[priority] > 0)
    .map((priority) => ({
      name: priority.charAt(0).toUpperCase() + priority.slice(1),
      value: data[priority],
      color: priorityColors[priority],
    }));

  return (
    <DonutChartComponent
      title="Task Priority Distribution"
      description="Breakdown of tasks by priority level"
      data={chartData}
      height={350}
      isLoading={isLoading}
      error={error}
      formatTooltip={(value, name) => [`${value} tasks`, `${name} Priority`]}
    />
  );
}
