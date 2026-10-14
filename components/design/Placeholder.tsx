import type {HTMLAttributes,ReactNode} from 'react';
export function Placeholder({children,...props}:HTMLAttributes<HTMLDivElement>){return <div {...props} data-placeholder="fictional-homeatlas-example">{children}</div>}
export function PlaceholderValue({children}:{children:ReactNode}){return <span data-placeholder="fictional-homeatlas-example">{children}</span>}
