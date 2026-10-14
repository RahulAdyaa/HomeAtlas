import fs from 'node:fs';import crypto from 'node:crypto';
if(fs.existsSync('.env')){console.log('Existing .env preserved.');process.exit(0)}
let text=fs.readFileSync('.env.example','utf8');for(const field of ['BETTER_AUTH_SECRET','WORKER_KEY','POSTGRES_PASSWORD'])text=text.replace(new RegExp(`^${field}=.*$`,'m'),`${field}=${crypto.randomBytes(32).toString('hex')}`);fs.writeFileSync('.env',text,{mode:0o600});console.log('Generated private local Compose .env. Configure the final origin and SMTP before deployment.');
