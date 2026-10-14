import {describe,it,expect} from 'vitest';
import {ancestry,locationPath,locationLink,descendants,type LocationNode} from '../lib/locations';
const nodes=[{id:'h',name:'Home',type:'home',parentId:null},{id:'r',name:'Study',type:'room',parentId:'h'},{id:'z',name:'Desk',type:'zone',parentId:'r'},{id:'c',name:'Top drawer',type:'container',parentId:'z'}] as LocationNode[];
describe('location paths',()=>{
 it('supports each attachment depth and optional container',()=>{expect(locationPath(nodes,'h')).toBe('Home');expect(locationPath(nodes,'r')).toBe('Study');expect(locationPath(nodes,'z')).toBe('Study > Desk');expect(locationPath(nodes,'c')).toBe('Study > Desk > Top drawer')});
 it('detects corrupt cycles',()=>expect(()=>ancestry([{...nodes[2],parentId:'z'}],'z')).toThrow('cycle'));
 it('includes all descendants for highlights and counts',()=>expect([...descendants(nodes,'r')]).toEqual(['r','z','c']));
 it('generates household-specific links',()=>expect(locationLink('h','c')).toBe('/?householdId=h&location=c'));
});
