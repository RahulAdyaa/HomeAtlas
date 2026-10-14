const loopback=new Set(['localhost','127.0.0.1','[::1]']);

export function localVerificationAvailable(request:Request){
 if(process.env.NODE_ENV!=='development'||process.env.ALLOW_LOCAL_MAIL!=='true'||process.env.SMTP_HOST)return false;
 try{
  const configured=new URL(process.env.BETTER_AUTH_URL??'http://localhost:3000');
  const requested=new URL(request.url);
  return loopback.has(configured.hostname)&&configured.protocol==='http:'&&requested.origin===configured.origin
   &&(!request.headers.get('host')||request.headers.get('host')===configured.host)
   &&(!request.headers.get('x-forwarded-host')||request.headers.get('x-forwarded-host')===configured.host);
 }catch{return false}
}
