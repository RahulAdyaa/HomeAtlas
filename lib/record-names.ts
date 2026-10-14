// Use the same conservative identity normalization in SQL and question matching.
export function normalizeRecordName(value:string){return value.toLowerCase().replace(/\b(?:aadhaar|aadhar|adhaar|adhar)\b/g,'aadhaar').replace(/[^a-z0-9]+/g,'').replace(/^(aadhaar|pan)card$/,'$1')}
export function recordNameSql(expression:string){return `regexp_replace(regexp_replace(regexp_replace(lower(${expression}),'\\m(aadhaar|aadhar|adhaar|adhar)\\M','aadhaar','g'),'[^a-z0-9]+','','g'),'^(aadhaar|pan)card$','\\1')`}
