import { expect, test } from '@playwright/test';

test('portal carga como producto y no expone artefactos de generador', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByText('Portal Ciudadano ClaveUnica')).toBeVisible();
  await expect(page.getByText('Validaciones')).toHaveCount(0);
  await expect(page.getByText('Actividad reciente')).toHaveCount(0);
  await expect(page.locator('body')).not.toContainText('implementa campos');
  await expect(page.locator('body')).not.toContainText(/\b(CU|FUN|FT|RN|CH|EX|ACT|REQ)_/);
  await expect(page.locator('body')).not.toContainText(/trazabilidad|traceability/i);
});

test('accion ciudadana cambia estado observable', async ({ page, request }) => {
  const before = await request.get('/api/v1/app-state');
  expect(before.ok()).toBeTruthy();
  const beforeJson = await before.json();
  const beforeProcedures = beforeJson.db.procedures.length;

  await page.goto('/portal/catalog');
  await page.getByRole('button', { name: /Iniciar tramite/i }).click();
  await expect.poll(async () => {
    const response = await request.get('/api/v1/app-state');
    const json = await response.json();
    return json.db.procedures.length;
  }).toBeGreaterThan(beforeProcedures);
});
