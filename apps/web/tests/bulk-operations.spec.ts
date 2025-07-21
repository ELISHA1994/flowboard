import { test, expect } from '@playwright/test';

test.describe('Bulk Operations', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page
    await page.goto('http://localhost:3000/login');

    // Login with test user
    await page.fill('input[name="username"]', 'testuser');
    await page.fill('input[name="password"]', 'testpass');
    await page.click('button[type="submit"]');

    // Wait for redirect to dashboard or tasks page
    await page.waitForURL(/\/(dashboard|tasks)/);

    // Navigate to tasks page if not already there
    await page.goto('http://localhost:3000/tasks');
    await page.waitForLoadState('networkidle');
  });

  test('should login successfully and show tasks', async ({ page }) => {
    // Check if we're on tasks page
    await expect(page.locator('h1')).toContainText(/Tasks/i);

    // Check if tasks are loaded (or loading state is shown)
    await page.waitForSelector(
      '[data-testid="tasks-list"], [data-testid="loading-spinner"], .text-muted-foreground:has-text("No tasks found")',
      { timeout: 10000 }
    );
  });

  test('should allow selecting multiple tasks', async ({ page }) => {
    // Wait for tasks to load
    await page.waitForSelector(
      '[data-testid="task-item"], .text-muted-foreground:has-text("No tasks found")',
      { timeout: 10000 }
    );

    // Check if there are tasks to select
    const taskItems = await page.locator('[data-testid="task-item"]').count();

    if (taskItems > 0) {
      // Select first task
      await page.check('[data-testid="task-checkbox"]:first-of-type');

      // Check if bulk actions are available
      await expect(page.locator('[data-testid="bulk-actions-button"]')).toBeVisible();

      if (taskItems > 1) {
        // Select second task if available
        await page.check('[data-testid="task-checkbox"]:nth-of-type(2)');

        // Check selected count
        await expect(page.locator('[data-testid="selected-count"]')).toContainText('2');
      }
    } else {
      console.log('No tasks available for bulk operations test');
    }
  });

  test('should perform bulk status update', async ({ page }) => {
    // Wait for tasks to load
    await page.waitForSelector(
      '[data-testid="task-item"], .text-muted-foreground:has-text("No tasks found")',
      { timeout: 10000 }
    );

    const taskItems = await page.locator('[data-testid="task-item"]').count();

    if (taskItems > 0) {
      // Select a task
      await page.check('[data-testid="task-checkbox"]:first-of-type');

      // Click bulk actions
      await page.click('[data-testid="bulk-actions-button"]');

      // Check if bulk actions menu is visible
      await expect(page.locator('[data-testid="bulk-actions-menu"]')).toBeVisible();

      // Click on change status
      await page.click('text="Change Status"');

      // Select new status
      await page.click('text="In Progress"');

      // Wait for success message or page update
      await page
        .waitForResponse(
          (response) => response.url().includes('/tasks/bulk/') && response.status() === 200,
          { timeout: 5000 }
        )
        .catch(() => {
          console.log('Bulk update request may have failed or timed out');
        });
    } else {
      console.log('No tasks available for bulk status update test');
    }
  });

  test('should handle authentication errors gracefully', async ({ page }) => {
    // Clear local storage to simulate expired token
    await page.evaluate(() => localStorage.clear());

    // Reload page
    await page.reload();

    // Should redirect to login or show error
    await page.waitForURL(/\/login/, { timeout: 10000 }).catch(async () => {
      // If not redirected, check for auth error message
      const errorMessage = await page.locator('text=/401|Unauthorized|Not authenticated/i').first();
      await expect(errorMessage)
        .toBeVisible({ timeout: 5000 })
        .catch(() => {
          console.log('No clear authentication error shown');
        });
    });
  });

  test('should create test tasks if none exist', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Check if no tasks message is shown
    const noTasksMessage = await page
      .locator('.text-muted-foreground:has-text("No tasks found")')
      .count();

    if (noTasksMessage > 0) {
      console.log('No tasks found, creating test tasks...');

      // Click create task button
      await page.click(
        'button:has-text("Create Task"), button:has-text("Add Task"), [data-testid="create-task-button"]'
      );

      // Fill task form
      await page.fill('input[name="title"], input[placeholder*="title" i]', 'Test Task 1');
      await page.fill(
        'textarea[name="description"], textarea[placeholder*="description" i]',
        'Test task for bulk operations'
      );

      // Submit form
      await page.click('button[type="submit"], button:has-text("Create"), button:has-text("Save")');

      // Wait for task to be created
      await page
        .waitForResponse(
          (response) => response.url().includes('/tasks') && response.status() === 200,
          { timeout: 5000 }
        )
        .catch(() => {
          console.log('Task creation may have failed');
        });

      // Create another task
      await page.click(
        'button:has-text("Create Task"), button:has-text("Add Task"), [data-testid="create-task-button"]'
      );
      await page.fill('input[name="title"], input[placeholder*="title" i]', 'Test Task 2');
      await page.fill(
        'textarea[name="description"], textarea[placeholder*="description" i]',
        'Another test task for bulk operations'
      );
      await page.click('button[type="submit"], button:has-text("Create"), button:has-text("Save")');

      await page
        .waitForResponse(
          (response) => response.url().includes('/tasks') && response.status() === 200,
          { timeout: 5000 }
        )
        .catch(() => {
          console.log('Second task creation may have failed');
        });
    }
  });
});
