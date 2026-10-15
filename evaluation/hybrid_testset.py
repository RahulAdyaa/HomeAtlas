"""Fictional household corpus, gold IDs authored before ranking (no user records)."""
DOCUMENTS = [
 ('aadhaar','Aadhaar card','Study > Desk > Top drawer','Aadhaar identity card number 0000 1111 2222.','identity'),
 ('pan','PAN card','Living room > Cabinet','Permanent account number TESTP0001A.','identity tax'),
 ('passport','Passport','Bedroom > Wardrobe','Passport number DEMO12345. Expires June 2030.','travel identity'),
 ('passport-photo','Passport photograph','Study > Desk','Two passport photographs for visa application.','photo travel'),
 ('licence','Driving licence','Living room > Cabinet','Driving licence DL-DEMO-7654.','vehicle identity'),
 ('fridge','Fridge warranty','Kitchen > Cabinet','Refrigerator FR-900 warranty expires May 2028.','appliance warranty'),
 ('washer','Washing machine warranty','Laundry > Shelf','Washing machine WM-800 warranty expires July 2029.','appliance warranty'),
 ('microwave','Microwave receipt','Kitchen > Drawer','Microwave MW-700 invoice paid 8000 rupees.','appliance receipt'),
 ('laptop','Laptop receipt','Study > Desk','Laptop LT-600 bill paid 50000 rupees.','electronics receipt'),
 ('television','Television manual','Living room > TV unit','Television TV-500 model supports HDMI input.','electronics manual'),
 ('insurance','Home insurance policy','Study > Storage','Home insurance policy DEMO-HOME-44 renewal in September.','insurance'),
 ('keys','Spare keys','Living room > Entry box','Spare house keys kept inside the blue entry box.','keys'),
 ('medicine','Medicine prescription','Bedroom > Bedside drawer','Prescription for fictional medicine TESTMED.','health'),
 ('electricity','Electricity bill','Study > Desk','Electricity bill meter EM-2222 paid 1500 rupees.','utilities'),
 ('birth','Birth certificate','Bedroom > Wardrobe','Birth certificate fictional registration BC-5555.','identity'),
 ('filter','Purifier filter manual','Kitchen > Shelf','Air purifier replacement filter HA-200. Replace every six months.','appliance'),
 ('router','Router manual','Study > Desk','Router model RT-400 reset takes ten seconds.','electronics'),
 ('ac','Air conditioner warranty','Bedroom > Wardrobe','Air conditioner AC-300 warranty ends November 2027.','appliance'),
 ('bank','Bank statement','Study > Storage','Fictional bank statement account DEMO-7788.','finance'),
 ('school','School certificate','Bedroom > Storage','School leaving certificate number SC-9999.','education')]
TYPO_GROUPS={
 'aadhaar':['where is Adhaar','Aadhar kahan hai','find AAADHAAAR','adhar card','aadhr serial number','uid card kidhar hai'],
 'pan':['pna card','permanet account number','where is pann card','PAN kahan hai'],
 'passport':['paspsort','passprt kahan hai','passsport','where is pasport'],
 'licence':['drivng licence','dirving license','DL kahan hai','driving licnce'],
 'fridge':['frdge waranty','refrigrator guarantee','fridge warrannty','fridge ki warranty'],
 'washer':['washing machien waranty','washng machine guarantee','washer warrnty','washer ki warranty'],
 'laptop':['laptpo reciept','laptop invoce','laptoop bill','laptop ki receipt'],
 'microwave':['micorwave receipt','microwave recipt','microwve invoice','microwave ka bill'],
 'insurance':['home insurnace policy','home insurence','home insurrance policy','insurance ki policy']}
QUERIES=[{'question':q,'relevant':[key],'subset':'typo'} for key,qs in TYPO_GROUPS.items() for q in qs]
QUERIES += [{'question':title,'relevant':[key],'subset':'clean'} for key,title,*_ in DOCUMENTS]
QUERIES += [{'question':q,'relevant':[key],'subset':'identifier'} for key,q in [('pan','TESTP0001A'),('aadhaar','0000 1111 2222'),('washer','WM-800'),('filter','HA-200'),('router','RT-400')]]
QUERIES += [{'question':q,'relevant':[],'subset':'no-match'} for q in ['quantum unicorn plutonium','spaceship ZX-9876','dinosaur DNA certificate','TESTP9999Z','WM-999']]
