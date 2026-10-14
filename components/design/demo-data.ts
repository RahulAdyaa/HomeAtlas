// Original fictional AirOne fixtures. Never a real user's home or real appliance advice.
export const demoRooms=['Living room','Kitchen','Bedroom','Bathroom','Laundry','Study'];
export const demoDocuments=[
 {title:'AirOne AP-200 manual',path:'/demo/AirOne-AP200-manual.pdf#page=2',page:2},
 {title:'AirOne purchase receipt',path:'/demo/AirOne-purchase-receipt.pdf',page:1},
];
export const demoQuestion={question:'Which filter fits my bedroom purifier?',answer:'A200-HEPA',quote:'The AirOne AP-200 uses the A200-HEPA replacement filter.',page:2};
export const demoHouseholdSummary=[{value:demoRooms.length,label:'rooms'},{value:demoDocuments.length,label:'documents'},{value:1,label:'answer you can check'}];
// Public city centres used only as illustrative locations; never customer/address data.
export const demoLocations=[{name:'New York',longitude:-74.006,latitude:40.7128},{name:'London',longitude:-0.1276,latitude:51.5072},{name:'Mumbai',longitude:72.8777,latitude:19.076}];
export const demoMaintenance=[{date:'24 Oct',title:'Replace the purifier filter',detail:'Bedroom · every 180 days',status:'Upcoming'},{date:'12 Feb 2028',title:'Warranty record expires',detail:'AirOne AP-200 · original sample receipt',status:'Recorded'}];
export const capabilities=[
  {
    "title": "Rooms and inventory",
    "plain": "Keep each appliance with the room it belongs to.",
    "detail": "Store the make, model, serial number, purchase date and warranty date. Attach records to the item and find it through the room list or the 3D Home View.",
    "gives": "An item record with its documents.",
    "terms": [
      "Rooms",
      "Appliance records",
      "Purchase and warranty dates",
      "Item notes and history",
      "3D Home View"
    ]
  },
  {
    "title": "Private document library",
    "plain": "Put the manual, receipt and contractor note in one place.",
    "detail": "Upload PDFs, photos, audio and video to a private household library. Processing retains PDF pages and regions, transcribed timestamps and source versions; its status stays visible.",
    "gives": "Records you can open and trace.",
    "terms": [
      "PDF pages and regions",
      "Photo and scan OCR",
      "Audio and video transcripts",
      "Source versions",
      "Processing and retry"
    ]
  },
  {
    "title": "Answers with evidence",
    "plain": "Ask about your home. Check the source beside the answer.",
    "detail": "Use text, a photo or a voice question to search your household records. Open the exact cited page, image or transcript moment; missing or conflicting evidence stays explicit.",
    "gives": "A finding you can check.",
    "terms": [
      "Text, photo and voice questions",
      "Exact citations",
      "Household-scoped retrieval",
      "Missing-evidence results",
      "Saved answers"
    ]
  },
  {
    "title": "Maintenance and warranties",
    "plain": "See what needs attention before you forget it.",
    "detail": "Track warranty dates, schedule recurring maintenance and keep completed work in the item's history. The calendar shows the tasks entered by your household; it does not invent a maintenance schedule.",
    "gives": "The next task, with its date.",
    "terms": [
      "Warranty dates",
      "In-app reminders",
      "Recurring tasks",
      "Maintenance calendar",
      "Completion history"
    ]
  },
  {
    "title": "Household control",
    "plain": "Share your home records with the people you choose.",
    "detail": "Invite editors and viewers, then manage household roles. Manage passkeys, two-factor authentication and sessions, inspect internal credit usage, and export or delete the household's records.",
    "gives": "Access and usage you can account for.",
    "terms": [
      "Owner, editor and viewer roles",
      "Passkeys and two-factor authentication",
      "Session management",
      "Credit ledger",
      "Export and deletion"
    ]
  }
];
