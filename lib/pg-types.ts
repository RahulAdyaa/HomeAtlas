import pg from 'pg';
// Credit balances use bigint in PostgreSQL but remain exact JSON numbers.
// Reject unsafe integers rather than silently rounding them in API responses.
pg.types.setTypeParser(20,value=>{
 const number=Number(value);
 if(!Number.isSafeInteger(number))throw new RangeError('Database integer exceeds the supported exact numeric range');
 return number;
});
