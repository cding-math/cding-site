// Copy beside a temporary tooling/ installation of Lighthouse 13.5.0.
import lighthouse from './tooling/node_modules/lighthouse/core/index.js';
import { launch } from './tooling/node_modules/chrome-launcher/dist/index.js';
import { userAgents } from './tooling/node_modules/lighthouse/core/config/constants.js';
import fs from 'node:fs/promises';
import path from 'node:path';

const [label='baseline', url='https://cding.me/', filter='all', widthArg='402'] = process.argv.slice(2);
const mobileWidth=Number(widthArg);
if(!Number.isInteger(mobileWidth)||mobileWidth<320||mobileWidth>800)throw new Error('Invalid mobile width');
const output = path.resolve(process.env.CDING_AUDIT_OUTPUT || '.', label);
await fs.mkdir(output, {recursive:true});
const cases = [
  {id:'desktop-fast', mobile:false, method:'provided', latency:0, down:0, up:0, cpu:1},
  {id:'desktop-slow4g', mobile:false, method:'devtools', latency:150, down:1600, up:750, cpu:1},
  {id:'mobile-slow4g', mobile:true, method:'devtools', latency:150, down:1600, up:750, cpu:4, warm:true},
  {id:'mobile-slow3g', mobile:true, method:'devtools', latency:400, down:400, up:400, cpu:4},
].filter(item=>filter==='all'||item.id===filter);
const summary=[];
for (const test of cases) {
  const profile=path.join(output,'profile-'+test.id+'-'+Date.now());
  await fs.mkdir(profile,{recursive:true});
  const chrome=await launch({
    chromePath:process.env.CHROME_PATH || '/Applications/Helium.app/Contents/MacOS/Helium',
    chromeFlags:['--headless=new','--disable-extensions','--no-first-run','--no-default-browser-check'],
    userDataDir:profile,
    logLevel:'silent',
  });
  try {
    for (const warm of test.warm && !process.env.CDING_AUDIT_COLD_ONLY ? [false,true] : [false]) {
      const id=test.id+(warm?'-warm':'-cold');
      console.log('START '+id);
      const settings={
        onlyCategories:['performance'],
        formFactor:test.mobile?'mobile':'desktop',
        screenEmulation:{mobile:test.mobile,width:test.mobile?mobileWidth:1280,height:test.mobile?874:900,deviceScaleFactor:test.mobile?3:1,disabled:false},
        emulatedUserAgent:userAgents[test.mobile?'mobile':'desktop'],
        throttlingMethod:test.method,
        throttling:{rttMs:test.latency,throughputKbps:test.down,requestLatencyMs:test.latency,downloadThroughputKbps:test.down,uploadThroughputKbps:test.up,cpuSlowdownMultiplier:test.cpu},
        disableStorageReset:warm,
        disableFullPageScreenshot:true,
        maxWaitForFcp:45000,
        maxWaitForLoad:60000,
      };
      const result=await lighthouse(url,{port:chrome.port,output:'json',logLevel:'error'}, {extends:'lighthouse:default',settings});
      await fs.writeFile(path.join(output,id+'.json'),JSON.stringify(result.lhr));
      if(result.artifacts?.DevtoolsLog)await fs.writeFile(path.join(output,id+'.network.json'),JSON.stringify(result.artifacts.DevtoolsLog));
      const trace=result.artifacts?.Trace || result.artifacts?.traces?.defaultPass;
      if(trace)await fs.writeFile(path.join(output,id+'.trace.json'),JSON.stringify(trace));
      const a=result.lhr.audits;
      const item={id,url,fetchTime:result.lhr.fetchTime,version:result.lhr.lighthouseVersion,settings:result.lhr.configSettings,score:result.lhr.categories.performance.score,error:result.lhr.runtimeError,warnings:result.lhr.runWarnings,FCP:a['first-contentful-paint']?.numericValue,LCP:a['largest-contentful-paint']?.numericValue,CLS:a['cumulative-layout-shift']?.numericValue,TBT:a['total-blocking-time']?.numericValue,SI:a['speed-index']?.numericValue,fonts:a['network-requests']?.details?.items?.filter(r=>/\.woff2(?:$|\?)/.test(r.url)).map(r=>({url:r.url,transferSize:r.transferSize,resourceSize:r.resourceSize,startTime:r.startTime,endTime:r.endTime,networkRequestTime:r.networkRequestTime,networkEndTime:r.networkEndTime})),shiftInsight:a['cls-culprits-insight']||a['layout-shift-elements']};
      summary.push(item);
      await fs.writeFile(path.join(output,'summary.json'),JSON.stringify(summary,null,2));
      const shots=a['screenshot-thumbnails']?.details?.items||[];
      for (let i=0;i<shots.length;i++) {
        const raw=shots[i].data.includes(',')?shots[i].data.split(',')[1]:shots[i].data;
        await fs.writeFile(path.join(output,`${id}-${i}-${Math.round(shots[i].timing)}ms.jpg`),Buffer.from(raw,'base64'));
      }
      console.log(JSON.stringify({id,FCP:item.FCP,LCP:item.LCP,CLS:item.CLS,TBT:item.TBT,score:item.score,error:item.error,fontTransfers:item.fonts?.map(r=>({name:path.basename(new URL(r.url).pathname),bytes:r.transferSize,finish:r.networkEndTime??r.endTime}))}));
    }
  } finally { await chrome.kill(); }
}
