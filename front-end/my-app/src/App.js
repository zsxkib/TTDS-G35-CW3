import './App.css';
import { Grid } from '@material-ui/core';
import logo from './logo.png'
import SearchBar from './search';

const App = () => {
    return (
      <Grid 
        container 
        justify="center" 
        alignItems="center" 
        direction="column"
        style={{minHeight:"100vh"}}
      >
          <img src={logo} alt="Logo" className="logo"/>
        <SearchBar/>
      </Grid>
    );
}

export default App;
