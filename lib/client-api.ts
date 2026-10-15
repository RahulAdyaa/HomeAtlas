/** Browser JSON requests, with transport method separate from application payload. */
export async function requestJSON(path:string,body?:unknown,method?:'GET'|'POST'|'DELETE'){
 const verb=method??(body===undefined?'GET':'POST');
 const isForm=body instanceof FormData;
 const response=await fetch(path,{method:verb,...(body===undefined?{}:{headers:isForm?{}:{'Content-Type':'application/json'},body:isForm?body:JSON.stringify(body)})});
 const data=await response.json();
 if(!response.ok)throw new Error(data.error||data.message||'Something went wrong. Please try again.');
 return data;
}
