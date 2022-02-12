import { dummyData } from "../data";
import React from "react";

export const Result = () => {
    return (
      <>
        <div>
          {dummyData.map((data, key) => {
            return (
              <div key={key}>
                {data.title}
              </div>
            );
          })}
        </div>
      </>
    );
  };
export default Result;
