import { test, expect } from '@playwright/test';

test.describe('Task Activity Tracking', () => {
  let taskId: string;

  test.beforeEach(async ({ page }) => {
    // Navigate to login page and login
    await page.goto('http://localhost:3000/login');
    await page.fill('input[name="email"]', 'testuser@example.com');
    await page.fill('input[name="password"]', 'testpassword');
    await page.click('button[type="submit"]');

    // Wait for redirect to dashboard
    await page.waitForURL('http://localhost:3000/dashboard');
  });

  test('should track complete task lifecycle activities', async ({ page }) => {
    // Step 1: Create a new task and capture its ID
    await page.goto('http://localhost:3000/tasks');
    await page.click('button:has-text("New Task")');

    // Fill in task details
    await page.fill('input[placeholder="Task title"]', 'Activity Tracking Test Task');
    await page.fill(
      'textarea[placeholder="Add a description..."]',
      'Testing comprehensive activity tracking'
    );
    await page.selectOption('select[name="priority"]', 'high');
    await page.selectOption('select[name="status"]', 'in_progress');

    // Submit the task
    await page.click('button[type="submit"]');

    // Wait for task to be created and navigate to it
    await page.waitForSelector('.task-card', { timeout: 10000 });
    await page.click('.task-card:first-child');

    // Extract task ID from URL
    await page.waitForURL(/\/tasks\/[a-f0-9-]+/);
    const url = page.url();
    taskId = url.split('/tasks/')[1];
    console.log(`Testing task: ${taskId}`);

    // Step 2: Navigate to Activity tab and verify creation activity
    await page.click('button[data-value="activity"]');
    await page.waitForSelector('[data-testid="activity-list"]', { timeout: 10000 });

    // Should see creation activity
    await expect(page.locator('text=created this task')).toBeVisible();
    await expect(page.locator('text=Activity tracking is now live!')).toBeVisible();

    // Step 3: Edit task title and verify activity logging
    await page.click('button:has([data-testid="edit-icon"])');
    await page.fill('input[value*="Activity Tracking Test Task"]', 'Updated Activity Test Task');
    await page.click('button:has-text("Save")');

    // Wait and check for title change activity
    await page.waitForTimeout(2000); // Wait for activity to be logged
    await page.reload(); // Refresh to see new activities
    await page.click('button[data-value="activity"]');

    await expect(page.locator('text=changed title')).toBeVisible();

    // Step 4: Change task status and verify activity
    await page.click('button:has([data-testid="edit-icon"])');
    await page.selectOption('select[value="in_progress"]', 'done');
    await page.click('button:has-text("Save")');

    // Check for status change activity
    await page.waitForTimeout(2000);
    await page.reload();
    await page.click('button[data-value="activity"]');

    await expect(page.locator('text=changed status')).toBeVisible();
    await expect(page.locator('text=in_progress')).toBeVisible();
    await expect(page.locator('text=done')).toBeVisible();

    // Step 5: Add a comment and verify activity
    await page.click('button[data-value="comments"]');
    await page.fill(
      'textarea[placeholder="Add a comment..."]',
      'This is a test comment for activity tracking'
    );
    await page.click('button:has-text("Post comment")');

    // Wait for comment to be posted
    await page.waitForSelector('text=This is a test comment', { timeout: 10000 });

    // Check activity tab for comment activity
    await page.click('button[data-value="activity"]');
    await page.waitForTimeout(2000);
    await page.reload();
    await page.click('button[data-value="activity"]');

    await expect(page.locator('text=added a comment')).toBeVisible();

    // Step 6: Change priority and verify activity
    await page.click('button:has([data-testid="edit-icon"])');
    await page.selectOption('select[value="high"]', 'medium');
    await page.click('button:has-text("Save")');

    // Check for priority change activity
    await page.waitForTimeout(2000);
    await page.reload();
    await page.click('button[data-value="activity"]');

    await expect(page.locator('text=changed priority')).toBeVisible();
    await expect(page.locator('text=high')).toBeVisible();
    await expect(page.locator('text=medium')).toBeVisible();

    // Step 7: Add a subtask and verify activity
    await page.locator('text=Subtasks').first().click();
    await page.fill('input[placeholder="Add a subtask..."]', 'Test Subtask for Activity');
    await page.keyboard.press('Enter');

    // Wait for subtask creation
    await page.waitForSelector('text=Test Subtask for Activity', { timeout: 10000 });

    // Check activity for subtask addition
    await page.click('button[data-value="activity"]');
    await page.waitForTimeout(2000);
    await page.reload();
    await page.click('button[data-value="activity"]');

    await expect(page.locator('text=added subtask')).toBeVisible();

    // Step 8: Verify activity timeline order and formatting
    const activities = await page.locator('[data-testid="activity-item"]').all();
    expect(activities.length).toBeGreaterThan(4); // Should have multiple activities

    // Verify each activity has required elements
    for (const activity of activities) {
      await expect(activity.locator('.activity-icon')).toBeVisible();
      await expect(activity.locator('.activity-user')).toBeVisible();
      await expect(activity.locator('.activity-time')).toBeVisible();
    }

    // Step 9: Test activity filtering/pagination if available
    const activityCount = await page.locator('text=activities').textContent();
    expect(activityCount).toContain('activit');

    // Step 10: Verify real-time updates by making another change
    await page.click('button:has([data-testid="edit-icon"])');
    await page.fill(
      'textarea[placeholder*="description"]',
      'Updated description for final activity test'
    );
    await page.click('button:has-text("Save")');

    // Check that new activity appears without full page reload
    await page.waitForTimeout(3000);
    await page.click('button[data-value="activity"]');

    await expect(page.locator('text=updated the description')).toBeVisible();
  });

  test('should display activity with proper formatting and icons', async ({ page }) => {
    // Create a task first
    await page.goto('http://localhost:3000/tasks');
    await page.click('button:has-text("New Task")');
    await page.fill('input[placeholder="Task title"]', 'UI Format Test Task');
    await page.fill(
      'textarea[placeholder="Add a description..."]',
      'Testing activity UI formatting'
    );
    await page.click('button[type="submit"]');

    // Navigate to the task
    await page.waitForSelector('.task-card');
    await page.click('.task-card:first-child');

    // Go to activity tab
    await page.click('button[data-value="activity"]');
    await page.waitForSelector('[data-testid="activity-list"]', { timeout: 10000 });

    // Verify activity item structure
    const firstActivity = page.locator('[data-testid="activity-item"]').first();

    // Should have icon with proper styling
    await expect(firstActivity.locator('.activity-icon')).toBeVisible();
    await expect(firstActivity.locator('.activity-icon')).toHaveClass(/border-green-600/);

    // Should have user avatar and name
    await expect(firstActivity.locator('[data-testid="user-avatar"]')).toBeVisible();
    await expect(firstActivity.locator('text=testuser')).toBeVisible();

    // Should have relative time
    await expect(firstActivity.locator('text=just now')).toBeVisible();

    // Should have activity description
    await expect(firstActivity.locator('text=created this task')).toBeVisible();

    // Should have timeline connector
    await expect(firstActivity.locator('.timeline-connector')).toBeVisible();
  });

  test('should handle activity loading states and errors', async ({ page }) => {
    // Navigate to a task
    await page.goto('http://localhost:3000/tasks');
    await page.waitForSelector('.task-card');
    await page.click('.task-card:first-child');

    // Go to activity tab and check loading state
    await page.click('button[data-value="activity"]');

    // Should see loading skeletons initially
    await expect(page.locator('[data-testid="activity-skeleton"]')).toBeVisible();

    // Wait for activities to load
    await page.waitForSelector('[data-testid="activity-list"]', { timeout: 10000 });

    // Loading skeletons should be gone
    await expect(page.locator('[data-testid="activity-skeleton"]')).not.toBeVisible();

    // Should show activities or empty state
    const hasActivities = (await page.locator('[data-testid="activity-item"]').count()) > 0;
    const hasEmptyState = await page.locator('text=No activity recorded yet').isVisible();

    expect(hasActivities || hasEmptyState).toBeTruthy();
  });

  test('should show proper activity details for different activity types', async ({ page }) => {
    // Create and modify a task to generate various activity types
    await page.goto('http://localhost:3000/tasks');
    await page.click('button:has-text("New Task")');
    await page.fill('input[placeholder="Task title"]', 'Activity Details Test');
    await page.selectOption('select[name="priority"]', 'low');
    await page.click('button[type="submit"]');

    // Navigate to task
    await page.waitForSelector('.task-card');
    await page.click('.task-card:first-child');

    // Change priority to generate priority change activity with old/new values
    await page.click('button:has([data-testid="edit-icon"])');
    await page.selectOption('select[value="low"]', 'urgent');
    await page.click('button:has-text("Save")');

    // Check activity details
    await page.click('button[data-value="activity"]');
    await page.waitForTimeout(2000);
    await page.reload();
    await page.click('button[data-value="activity"]');

    // Should show priority change with badges
    await expect(page.locator('text=changed priority')).toBeVisible();
    await expect(page.locator('[data-testid="priority-badge"]')).toHaveCount(2); // old and new

    // Change status to test status icons
    await page.click('button:has([data-testid="edit-icon"])');
    await page.selectOption('select[value="todo"]', 'done');
    await page.click('button:has-text("Save")');

    await page.waitForTimeout(2000);
    await page.reload();
    await page.click('button[data-value="activity"]');

    // Should show status change with icons
    await expect(page.locator('text=changed status')).toBeVisible();
    await expect(page.locator('[data-testid="status-icon"]')).toHaveCount(2); // old and new
  });
});
