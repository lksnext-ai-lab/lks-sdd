import {expect,test} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';

test('HTTPS local-auth flow and independent observation handoff',async({page,context,browserName})=>{
  const requests=[];const consoleErrors=[];let observing=false;
  page.on('console',message=>{if(observing&&message.type()==='error')consoleErrors.push(message.text());});
  page.on('pageerror',error=>{if(observing)consoleErrors.push(error.message);});
  page.on('response',response=>{const path=new URL(response.url()).pathname;if(path.startsWith('/records'))requests.push({path,method:response.request().method(),status:response.status()});});
  await page.goto('/');
  await expect(page.getByRole('heading',{name:'Private workspace'})).toBeVisible();
  expect((await new AxeBuilder({page}).analyze()).violations).toEqual([]);
  if(process.env.LKS_WEB_MODE!=='system'){
    writeFileSync('/runtime/browser-evidence.json',JSON.stringify({browser:browserName,component_only:true,login_surface:true,a11y_violations:0}));return;
  }
  const fixture=JSON.parse(readFileSync('/runtime/fixture.json','utf8'));
  await page.getByLabel('Username',{exact:true}).fill(fixture.users[0].username);
  await page.getByLabel('Password',{exact:true}).fill(fixture.users[0].password);
  await page.getByLabel('Organization',{exact:true}).fill(fixture.organizations[0]);
  await page.getByRole('button',{name:'Sign in',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Records',exact:true})).toBeVisible();
  observing=true;
  const screenshots=[];
  async function capture(state){expect(await page.locator('input[type=password]').count()).toBe(0);const path=`/runtime/${state}.png`;await page.screenshot({path});screenshots.push({state,path:`${state}.png`,sha256:createHash('sha256').update(readFileSync(path)).digest('hex'),credential_fields_absent:true});}
  await capture('before');
  const label=`synthetic-${Date.now()}`;
  await page.getByLabel('Record label').fill(label);
  const saved=page.waitForResponse(r=>new URL(r.url()).pathname==='/records'&&r.request().method()==='POST');
  await page.getByRole('button',{name:'Save record'}).click();
  const response=await saved;expect(response.status()).toBe(201);
  await expect(page.getByRole('listitem').filter({hasText:label})).toBeVisible();
  const item={id:await page.getByRole('listitem').filter({hasText:label}).getAttribute('data-record-id')};
  await capture('after');
  await page.reload();await expect(page.getByRole('listitem').filter({hasText:label})).toBeVisible();
  await capture('reloaded');
  expect(await page.evaluate(()=>({local:localStorage.length,session:sessionStorage.length}))).toEqual({local:0,session:0});
  const cookies=await context.cookies();const refresh=cookies.find(c=>c.name==='__Host-lks-refresh');
  expect(refresh.httpOnly).toBe(true);expect(refresh.secure).toBe(true);expect(refresh.sameSite).toBe('Strict');
  const second=await context.newPage();await second.goto('/');await expect(second.getByRole('heading',{name:'Records',exact:true})).toBeVisible();
  observing=false;expect(consoleErrors).toEqual([]);
  await context.setOffline(true);await page.getByRole('button',{name:'Sign out'}).click();
  await expect(page.getByRole('status')).toContainText('could not be confirmed');
  await expect(second.getByRole('heading',{name:'Sign in',exact:true})).toBeVisible();await context.setOffline(false);
  await second.close();
  writeFileSync('/runtime/browser-evidence.json',JSON.stringify({runtime_units:['frontend','api','database'],browser:browserName,viewport:page.viewportSize(),requests,mutation:{method:'POST',path:'/records',record_id:item.id,label},read_back:false,reload:true,persistence:false,screenshots,console_errors:consoleErrors,multiple_tabs:true,offline_logout_honest:true,credential_storage:false}));
});
