import React, { useState, useEffect } from "react";

export default function ServicesListing({ setService, setActiveTab, show }) {

  const [services, setServices] = useState([])

  useEffect(() => {
    fetch(`${process.env.REACT_APP_ENGINE_URL}/services`)
      .then((resp) => resp.json().then((value) => {
          setServices(value);
        })
      )
      .catch((err) => {
        console.log("Unable to get the services : ", err);
      })
  }, [])

  return (
    <div>
      <div className="buttons" style={{ display: show ? "block" : "none" }}>
        {
          services.map(s => <button
            className="button is-small is-info is-fullwidth"
            title={s.nodes[0].api.summary}
            onClick={() => { setActiveTab(); setService(s) }}
            key={s.nodes[0].api.route}
          >
            {s.nodes[0].api.route}
          </button>)
        }
      </div>
    </div>
  );
}