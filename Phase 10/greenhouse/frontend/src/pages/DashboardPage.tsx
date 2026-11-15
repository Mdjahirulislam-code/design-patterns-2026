import { useState } from "react";

import SensorList from "../features/sensors/SensorList";
import StrategyPanel from "../features/automation/StrategyPanel";
import ExecutionLog from "../features/actuators/ExecutionLog";
import CommandPanel from "../components/commands/CommandPanel";
import OverviewPanel from "../components/overview/OverviewPanel";
import DeviceList from "../components/devices/DeviceList";
import DeviceFamilySwitcher from "../components/devices/DeviceFamilySwitcher";
import { provisionDeviceFamily } from "../services/api";


type Placeholder = {
  id: string;
  title: string;
  description: string;
  phase: string;
};


const SECTIONS: Placeholder[] = [
  {
    id: "config",
    title: "Configuration",
    description:
      "Greenhouse-wide settings such as target ranges and units.",
    phase: "Later phase",
  },
  {
    id: "events",
    title: "Events",
    description:
      "Alarm and activity log produced by the system.",
    phase: "Later phase",
  },
];


export default function DashboardPage() {

  const [family, setFamily] = useState<
    "simulation" | "edge"
  >("simulation");


  const handleProvision = async () => {

    await provisionDeviceFamily(family);

    window.location.reload();

  };


  return (
    <section>

      <h2 className="text-2xl font-bold text-slate-900">
        Dashboard
      </h2>


      <p className="mt-2 text-slate-600">
        Phase 10 turns actuator actions into command objects. The controls only
        offer what the current state allows, and every command is stored in the
        command history.
      </p>



      <div className="mt-6 space-y-6">


        {/* Phase 7 Overview (one facade request) */}

        <OverviewPanel />



        {/* Sensors: Phase 2 list + Phase 5 read / sampling */}

        <SensorList />



        {/* Phase 3 Devices */}

        <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">


          <div className="flex items-center justify-between mb-5">

            <h2 className="text-xl font-bold text-slate-900">
              Devices
            </h2>


            <button
              onClick={handleProvision}
              className="rounded bg-green-600 px-4 py-2 text-white hover:bg-green-700"
            >
              Provision {family}
            </button>

          </div>



          <DeviceFamilySwitcher
            family={family}
            setFamily={setFamily}
          />



          <div className="mt-5">

            <DeviceList family={family} />

          </div>


        </section>




        {/* Phase 10 Controls: commands + history */}

        <CommandPanel />



        {/* Phase 9 Actuator execution log (decorated port) */}

        <ExecutionLog />



        {/* Phase 6 Automation strategy */}

        <StrategyPanel />



        {/* Future sections */}

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">


          {SECTIONS.map((section) => (

            <article
              key={section.id}
              id={section.id}
              className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"
            >

              <h3 className="text-lg font-semibold text-slate-900">
                {section.title}
              </h3>


              <p className="mt-2 text-sm text-slate-600">
                {section.description}
              </p>


              <span className="mt-4 inline-block rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-500">
                {section.phase}
              </span>


            </article>

          ))}


        </div>


      </div>


    </section>
  );
}