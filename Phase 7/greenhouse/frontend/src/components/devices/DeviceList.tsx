import { useEffect, useState } from "react";

import {
  fetchDevices,
  type DeviceDto,
  type DeviceFamily
} from "../../services/api";


type Props = {
  family: DeviceFamily;
};


export default function DeviceList({
  family
}: Props) {


  const [devices, setDevices] =
    useState<DeviceDto[]>([]);


  const [error, setError] =
    useState("");



  useEffect(() => {

    setError("");

    fetchDevices({
      family
    })

      .then((data) => {

        setDevices(data);

      })

      .catch(() => {

        setError(
          "Failed to load devices"
        );

      });


  }, [family]);





  return (

    <section>


      {error && (

        <div className="border border-red-300 text-red-600 p-3 rounded">

          {error}

        </div>

      )}




      {devices.length === 0 && !error && (

        <div className="border p-4 rounded">

          No devices found.

        </div>

      )}






      <div className="grid gap-4 md:grid-cols-2">


        {devices.map((device) => (


          <div
            key={device.id}
            className="rounded-lg border border-slate-200 p-4"
          >


            <div className="flex justify-between">


              <h3 className="font-bold text-lg">

                {device.display_name}

              </h3>


              <span className="rounded-full bg-green-100 px-3 py-1 text-xs">

                {device.role}

              </span>


            </div>




            <p className="mt-2 text-sm">

              Type: {device.device_type}

            </p>


            <p className="text-sm">

              Family: {device.device_family}

            </p>





            <div className="mt-4 border-t pt-3">


              {Object.entries(
                device.default_config
              )

              .map(([key,value]) => (


                <div
                  key={key}
                  className="flex justify-between text-sm py-1"
                >

                  <span className="text-slate-500">

                    {key}

                  </span>


                  <span className="font-medium">

                    {String(value)}

                  </span>


                </div>


              ))}


            </div>



          </div>


        ))}


      </div>


    </section>

  );
}