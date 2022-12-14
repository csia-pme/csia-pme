import { Box, Container, TextField, Typography } from '@mui/material';
import React from 'react';
import MyGrid from '../../components/Grid/MyGrid';


const Home: React.FC = () => {

    const [search, setSearch] = React.useState('');

    const handleSearch = (event: React.ChangeEvent<HTMLInputElement>) => {
        setSearch(event.target.value);
    }

    return (
        <Container>
            <main>
                <Box sx={{pt: 8, pb: 6}}>
                    <Container maxWidth="lg">
                        <Typography
                            component="h1"
                            variant="h2"
                            align="center"
                            color="text.primary"
                            gutterBottom
                        >
                            CSIA-PME
                        </Typography>
                        <Typography variant="h5" align="justify" color="text.secondary" paragraph>
                            CSIA-PME is a project of the Swiss AI Center of the HES-SO University of Applied
                            Sciences and Arts of Western Switzerland.
                            The purpose is to provide a platform for the development of AI applications in
                            different domains in PME.
                            This page is a prototype of the platform with demos.
                        </Typography>
                    </Container>
                </Box>
                <Container sx={{py: 8}} maxWidth="lg">
                    <TextField sx={{mb: 2}} name={'search'} label={'Search'} value={search} onChange={handleSearch} fullWidth />
                    <MyGrid filter={search}/>
                </Container>
            </main>
        </Container>
    );
}


    export default Home;
