import {it,expect} from 'vitest';
import {itemFactIntent} from '../lib/item-facts';
import {normalizeRecordName} from '../lib/record-names';
it('recognizes natural serial-number questions without requiring one exact sentence',()=>{
 for(const question of ['What is my Aadhaar card serial number?','What is the serial number of my Aadhaar card?',"What's my Aadhaar card number?",'Tell me my Aadhaar number']){const intent=itemFactIntent(question);expect(intent?.field.key).toBe('serialNumber');expect(normalizeRecordName(intent?.target||'')).toBe('aadhaar');}
});
it('matches supported saved fields without confusing model number with serial number',()=>{
 expect(itemFactIntent('Show me the model number for my washing machine')?.field.key).toBe('model');
 expect(itemFactIntent('What is my air purifier brand?')?.field.key).toBe('make');
 expect(itemFactIntent('What is the warranty end date of my fridge?')?.field.key).toBe('warrantyDate');
 expect(itemFactIntent('When does my fridge warranty expire?')?.field.key).toBe('warrantyDate');
 expect(itemFactIntent('When did I buy my fridge?')?.field.key).toBe('purchaseDate');
});
it('normalizes identity-card spelling variants without collapsing different records',()=>{
 for(const name of ['Aadhaar card','aadhar card','Adhaar','AADHAAR'])expect(normalizeRecordName(name)).toBe('aadhaar');
 expect(normalizeRecordName('PAN Card')).toBe('pan');expect(normalizeRecordName('Aadhaar receipt')).not.toBe('aadhaar');
});
it('leaves open-ended content and unsupported questions to document RAG',()=>{
 expect(itemFactIntent('Explain what my Aadhaar card says')).toBeNull();expect(itemFactIntent('What is my electricity consumption?')).toBeNull();
});
