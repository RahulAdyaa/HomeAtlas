export type RecordRow = {id:string;name?:string;title?:string;[key:string]:any};
export type Atlas = {user:RecordRow;household:RecordRow|null;membership?:RecordRow;rooms:RecordRow[];items:RecordRow[];sources:RecordRow[];tasks:RecordRow[];activity:RecordRow[];credits:any;members:RecordRow[];bookmarks:RecordRow[];[key:string]:any};
export type Citation = {id:string;sourceId:string;versionId:string;title:string;page?:number;bbox?:number[];text:string;start?:number;end?:number;[key:string]:any};
