import React, { useEffect, useState } from "react"
import { useLocation } from 'react-router-dom';

const UsingFetch = () => {
  const [users, setUsers] = useState([])
  let { state } = useLocation();
  let query = state["searchTerm"];
  console.log(query)

  const fetchData = () => {
    fetch("http://127.0.0.1:8000/search/?query=$".replace("$", query))
      .then(response => {
        return response.json()
      })
      .then(data => {
        setUsers(data["0"])
      })
  }

  useEffect(() => {
    fetchData()
  }, [])

  // TODO: WINI PLEASE MAKE THIS LOOK NICE!
  return (
    <div>
      {users.length > 0 && (
        <ul>
          {users.map(user => (
            <li key={user.title}>
              {user.title}
              <br></br>
              {user.link}
              <br></br>
              {user.description}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default UsingFetch