import {useState} from "react";
export default function LocationConfigWizard(){
 const [name,setName]=useState("");
 const create=async()=>{await fetch("http://127.0.0.1:8000/api/locations/config",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({location_name:name,zones:[{name:"Zone 1",moisture_threshold_low:.2,moisture_threshold_high:.5,schedule:{}}]})})}
 return <div className="border p-4"><h2 className="font-bold">Location Builder</h2><input className="border" value={name} onChange={e=>setName(e.target.value)}/><button onClick={create}>Create</button></div>
}
