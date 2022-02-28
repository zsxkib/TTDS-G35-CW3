import { IconButton, TextField} from '@material-ui/core';
import { SearchOutlined } from '@material-ui/icons';
import React, { useState } from "react";
import logo from '../logo_2.png'
import icon from '../icon.png'
import { Box } from '@material-ui/core';
import { useNavigate } from 'react-router-dom';
import { dummyData } from "../data";
import {useLocation} from 'react-router-dom';


// function ResultsPage () {
//   let navigate = useNavigate()
//   const [content, setContent] = useState('');
//   const { state } = useLocation();

//   var query = state["searchTerm"];

//   getResults =  function f(query) { 
//     return fetch("http://127.0.0.1:8000/search/?query=$".replace("$", query),
//     {
//       method: "GET",
//       headers: {
//         'Accept': 'application/json',
//         'Content-Type': 'application/json',
//       },
//     })
//     .then((response) => response.json())
//     .then((responseData) => {
//       // console.log(responseData);
//       return responseData;
//     })
//     .catch(error => console.warn(error));
//   }

//   res = getResults(query)


// const handleSubmit = (e) => {
//   navigate('./result', { state: { searchTerm: content } });
// };

//   return (
//     <div className='resultsPage'>
//       <div className="sidebar">
//         <img src={icon} alt="Icon" className="icon"/>
//       </div>
//       <div className='main_results'>
//         <img src={logo} alt="Logo" className="logo_2"/>
//         <form className='form_2' onSubmit={handleSubmit}>
//             <TextField
//                 id="search-bar"
//                 placeholder= "Search"
//                 value={content}
//                 onInput={ e=>setContent(e.target.value)}
//                 style={{width:"100%"}}
//                 InputProps={{
//                     endAdornment: (
//                         <IconButton type="submit">
//                           <SearchOutlined />
//                         </IconButton>
//                     ),
//                 }}
//                 variant="outlined"
//             />
//         </form>
//         <hr class="dashed"/>
//         <div className='all-results'>
//           {dummyData.map((data) => {
//               return (
//                 <div>
//                   <Box 
//                     border={2}
//                     borderRadius="6px"
//                     alignContent="center"
//                     width="60%"
//                     borderColor="#9FBBA5"
//                     color="#362706"
//                     padding= "5px"
//                   >
//                     <div className="title">
//                       {data.title}
//                     </div>
//                     <div className="description">
//                       {data.description}
//                     </div>
//                   </Box>
//                   <Box paddingTop="2%"></Box>
//                 </div>
//               );
//             })}
//         </div>
//       </div>
//     </div>
//   );
// }

// export default ResultsPage;


// Let's import React, our styles and React Async
// import './App.css';
import Async from 'react-async';

// We'll request user data from this API
const loadUsers = () =>
  fetch("http://127.0.0.1:8000/search/?query=$".replace("$", "query"))
    .then(res => (res.ok ? res : Promise.reject(res)))
    .then(res => res.json())

// Our component
function ResultsPage() {
  return (
    <div className="container">
      <Async promiseFn={loadUsers}>
        {({ data, err, isLoading }) => {
          if (isLoading) return "Loading..."
          if (err) return `Something went wrong: ${err.message}`

          if (data)
            return (
              <div>
                <div>
                  <h2>React Async - Random Users</h2>
                </div>
                {data["0"].map(user=> (
                  <div key={user.title} className="row">
                    <div className="col-md-12">
                      <p>{user.link}</p>
                      <p>{user.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            )
        }}
      </Async>
    </div>
  );
}

export default ResultsPage;