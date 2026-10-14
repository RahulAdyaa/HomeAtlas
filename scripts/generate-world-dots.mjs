import fs from 'node:fs';
import {feature} from 'topojson-client';
import {geoContains} from 'd3-geo';
const topology=JSON.parse(fs.readFileSync('node_modules/world-atlas/land-110m.json','utf8'));
const land=feature(topology,topology.objects.land);
// Natural Earth 1:110m land, sampled every 3 degrees; x/y are a 1000 × 470 map projection.
const points=[];
for(let latitude=-57;latitude<=81;latitude+=3)for(let longitude=-177;longitude<=177;longitude+=3){if(geoContains(land,[longitude,latitude]))points.push([Math.round((longitude+180)/360*1000),Math.round((84-latitude)/168*470)]);}
fs.writeFileSync('components/design/world-dots.json',JSON.stringify(points));
console.log('Generated',points.length,'land dots from Natural Earth geometry.');
