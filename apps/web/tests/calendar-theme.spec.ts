import { test, expect } from '@playwright/test';

test.describe('Calendar Theme Improvements', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page
    await page.goto('http://localhost:3000/login');

    // Login with test credentials
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');

    // Wait for dashboard to load
    await page.waitForURL('**/dashboard');

    // Navigate to calendar page
    await page.getByRole('link', { name: 'Calendar' }).click();
    await page.waitForURL('**/calendar');
  });

  test('should display enhanced calendar with new theme', async ({ page }) => {
    // Check if calendar is visible
    await expect(page.locator('.rbc-calendar')).toBeVisible();

    // Check if the calendar has gradient card styling
    const calendar = page.locator('.rbc-calendar');
    await expect(calendar).toHaveClass(/gradient-card/);

    // Check if toolbar is visible with new styling
    await expect(page.locator('.calendar-toolbar')).toBeVisible();

    // Check if New Task button has primary variant (green gradient)
    const newTaskButton = page.getByRole('button', { name: /New Task/i });
    await expect(newTaskButton).toBeVisible();
    await expect(newTaskButton).toHaveClass(/gradient-primary/);
  });

  test('should show calendar view tabs', async ({ page }) => {
    // Check if tabs are visible
    await expect(page.getByRole('tab', { name: 'Calendar' })).toBeVisible();
    await expect(page.getByRole('tab', { name: 'Time Tracking' })).toBeVisible();
    await expect(page.getByRole('tab', { name: 'Analytics' })).toBeVisible();
  });

  test('should create task from calendar slot', async ({ page }) => {
    // Click on a calendar slot to create a task
    const calendarSlot = page.locator('.rbc-day-slot').first();
    await calendarSlot.click();

    // Check if task creation modal opens
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByText('Create New Task')).toBeVisible();

    // Check if Create Task button has primary variant
    const createButton = page.getByRole('button', { name: 'Create Task' });
    await expect(createButton).toHaveClass(/gradient-primary/);
  });

  test('should display calendar events with enhanced styling', async ({ page }) => {
    // Wait for calendar events to load
    await page.waitForTimeout(1000);

    // Check if events have enhanced styling
    const events = page.locator('.rbc-event');
    const eventCount = await events.count();

    if (eventCount > 0) {
      // Check first event has gradient background
      const firstEvent = events.first();
      const style = await firstEvent.getAttribute('style');
      expect(style).toContain('linear-gradient');
    }
  });
});
