import {createFileRoute} from '@tanstack/react-router';
import AboutPage from '../components/OtherPages/AboutPage.tsx';

export const Route = createFileRoute('/about')({
    component: AboutPage,
});
