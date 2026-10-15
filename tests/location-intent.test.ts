import {it,expect} from 'vitest';
import {locationTarget,includeDemo} from '../lib/location-lookup';
import {normalizeRecordName} from '../lib/record-names';
it('recognizes location questions while preserving the item name',()=>{
 for(const question of ['where is my PAN Card?','Where can I find the PAN Card?','Where did I put my PAN Card?','Locate my PAN Card','Where is my PAN Card stored?'])expect(locationTarget(question)).toBe('PAN Card');
});
it('keeps document-content questions in the existing RAG pipeline',()=>{expect(locationTarget('What does my PAN card say?')).toBeNull();expect(locationTarget('When does my warranty expire?')).toBeNull()});
it('requires an explicit demo request',()=>{expect(includeDemo('Where is my PAN card?')).toBe(false);expect(includeDemo('Where is the sample PAN card?')).toBe(true)});
it('routes Hinglish locations and Aadhaar aliases to the saved record',()=>{
 expect(locationTarget('Mera Aadhar card kahan hai?')).toBe('Aadhar card');
 expect(locationTarget('UID card kidhar hai?')).toBe('UID card');
 for(const value of ['Adhaar','Aadhar','Aadhaar','AAADHAAR','adhar card','UID card'])expect(normalizeRecordName(value)).toBe('aadhaar');
});
