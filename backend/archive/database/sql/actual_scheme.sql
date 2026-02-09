--
-- PostgreSQL database cluster dump
--

-- Started on 2024-10-25 22:14:23

SET default_transaction_read_only = off;

SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

--
-- Roles
--

CREATE ROLE postgres;
ALTER ROLE postgres WITH SUPERUSER INHERIT CREATEROLE CREATEDB LOGIN REPLICATION BYPASSRLS PASSWORD 'SCRAM-SHA-256$4096:3vWdRK8lFewemddC3Wu4mg==$MS/nc6Gk3bVHLkeXCmd/55bIEL04BX3Yw15emT+3DDQ=:Q0kZwivqeBO6daiwqVE6ooYGa2a5zMhkEFvht/IsYZQ=';

--
-- User Configurations
--








--
-- Databases
--

--
-- Database "template1" dump
--

\connect template1

--
-- PostgreSQL database dump
--

-- Dumped from database version 16.3
-- Dumped by pg_dump version 16.3

-- Started on 2024-10-25 22:14:23

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

-- Completed on 2024-10-25 22:14:23

--
-- PostgreSQL database dump complete
--

--
-- Database "postgres" dump
--

\connect postgres

--
-- PostgreSQL database dump
--

-- Dumped from database version 16.3
-- Dumped by pg_dump version 16.3

-- Started on 2024-10-25 22:14:24

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 6 (class 2615 OID 24788)
-- Name: autocalc; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA autocalc;


ALTER SCHEMA autocalc OWNER TO postgres;

--
-- TOC entry 2 (class 3079 OID 16384)
-- Name: adminpack; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS adminpack WITH SCHEMA pg_catalog;


--
-- TOC entry 4823 (class 0 OID 0)
-- Dependencies: 2
-- Name: EXTENSION adminpack; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION adminpack IS 'administrative functions for PostgreSQL';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 216 (class 1259 OID 24789)
-- Name: resultcalcs; Type: TABLE; Schema: autocalc; Owner: postgres
--

CREATE TABLE autocalc.resultcalcs (
    id integer NOT NULL,
    user_name character varying(255) NOT NULL,
    stock_name character varying(255) NOT NULL,
    turbine_name character varying(255) NOT NULL,
    calc_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    input_data jsonb NOT NULL,
    output_data jsonb NOT NULL,
    valve_id integer NOT NULL
);


ALTER TABLE autocalc.resultcalcs OWNER TO postgres;

--
-- TOC entry 217 (class 1259 OID 24795)
-- Name: resultcalcs_id_seq; Type: SEQUENCE; Schema: autocalc; Owner: postgres
--

CREATE SEQUENCE autocalc.resultcalcs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE autocalc.resultcalcs_id_seq OWNER TO postgres;

--
-- TOC entry 4824 (class 0 OID 0)
-- Dependencies: 217
-- Name: resultcalcs_id_seq; Type: SEQUENCE OWNED BY; Schema: autocalc; Owner: postgres
--

ALTER SEQUENCE autocalc.resultcalcs_id_seq OWNED BY autocalc.resultcalcs.id;


--
-- TOC entry 218 (class 1259 OID 24796)
-- Name: stocks; Type: TABLE; Schema: autocalc; Owner: postgres
--

CREATE TABLE autocalc.stocks (
    id integer NOT NULL,
    name character varying(100),
    type character varying(50),
    diameter numeric(10,3),
    clearance numeric(10,3),
    count_parts integer,
    len_part1 numeric(10,3),
    len_part2 numeric(10,3),
    len_part3 numeric(10,3),
    len_part4 numeric(10,3),
    len_part5 numeric(10,3),
    round_radius numeric(10,3),
    turbine_id integer
);


ALTER TABLE autocalc.stocks OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 24799)
-- Name: stocks_id_seq; Type: SEQUENCE; Schema: autocalc; Owner: postgres
--

CREATE SEQUENCE autocalc.stocks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE autocalc.stocks_id_seq OWNER TO postgres;

--
-- TOC entry 4825 (class 0 OID 0)
-- Dependencies: 219
-- Name: stocks_id_seq; Type: SEQUENCE OWNED BY; Schema: autocalc; Owner: postgres
--

ALTER SEQUENCE autocalc.stocks_id_seq OWNED BY autocalc.stocks.id;


--
-- TOC entry 220 (class 1259 OID 24800)
-- Name: turbines; Type: TABLE; Schema: autocalc; Owner: postgres
--

CREATE TABLE autocalc.turbines (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    valves character varying(50)
);


ALTER TABLE autocalc.turbines OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 24803)
-- Name: turbines_id_seq; Type: SEQUENCE; Schema: autocalc; Owner: postgres
--

CREATE SEQUENCE autocalc.turbines_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE autocalc.turbines_id_seq OWNER TO postgres;

--
-- TOC entry 4826 (class 0 OID 0)
-- Dependencies: 221
-- Name: turbines_id_seq; Type: SEQUENCE OWNED BY; Schema: autocalc; Owner: postgres
--

ALTER SEQUENCE autocalc.turbines_id_seq OWNED BY autocalc.turbines.id;


--
-- TOC entry 223 (class 1259 OID 24819)
-- Name: unique_turbine; Type: TABLE; Schema: autocalc; Owner: postgres
--

CREATE TABLE autocalc.unique_turbine (
    id integer NOT NULL,
    name character varying(255) NOT NULL
);


ALTER TABLE autocalc.unique_turbine OWNER TO postgres;

--
-- TOC entry 222 (class 1259 OID 24818)
-- Name: unique_turbine_id_seq; Type: SEQUENCE; Schema: autocalc; Owner: postgres
--

CREATE SEQUENCE autocalc.unique_turbine_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE autocalc.unique_turbine_id_seq OWNER TO postgres;

--
-- TOC entry 4827 (class 0 OID 0)
-- Dependencies: 222
-- Name: unique_turbine_id_seq; Type: SEQUENCE OWNED BY; Schema: autocalc; Owner: postgres
--

ALTER SEQUENCE autocalc.unique_turbine_id_seq OWNED BY autocalc.unique_turbine.id;


--
-- TOC entry 4650 (class 2604 OID 24804)
-- Name: resultcalcs id; Type: DEFAULT; Schema: autocalc; Owner: postgres
--

ALTER TABLE ONLY autocalc.resultcalcs ALTER COLUMN id SET DEFAULT nextval('autocalc.resultcalcs_id_seq'::regclass);


--
-- TOC entry 4652 (class 2604 OID 24805)
-- Name: stocks id; Type: DEFAULT; Schema: autocalc; Owner: postgres
--

ALTER TABLE ONLY autocalc.stocks ALTER COLUMN id SET DEFAULT nextval('autocalc.stocks_id_seq'::regclass);


--
-- TOC entry 4653 (class 2604 OID 24806)
-- Name: turbines id; Type: DEFAULT; Schema: autocalc; Owner: postgres
--

ALTER TABLE ONLY autocalc.turbines ALTER COLUMN id SET DEFAULT nextval('autocalc.turbines_id_seq'::regclass);


--
-- TOC entry 4654 (class 2604 OID 24822)
-- Name: unique_turbine id; Type: DEFAULT; Schema: autocalc; Owner: postgres
--

ALTER TABLE ONLY autocalc.unique_turbine ALTER COLUMN id SET DEFAULT nextval('autocalc.unique_turbine_id_seq'::regclass);


--
-- TOC entry 4810 (class 0 OID 24789)
-- Dependencies: 216
-- Data for Name: resultcalcs; Type: TABLE DATA; Schema: autocalc; Owner: postgres
--

COPY autocalc.resultcalcs (id, user_name, stock_name, turbine_name, calc_timestamp, input_data, output_data, valve_id) FROM stdin;
\.


--
-- TOC entry 4812 (class 0 OID 24796)
-- Dependencies: 218
-- Data for Name: stocks; Type: TABLE DATA; Schema: autocalc; Owner: postgres
--

COPY autocalc.stocks (id, name, type, diameter, clearance, count_parts, len_part1, len_part2, len_part3, len_part4, len_part5, round_radius, turbine_id) FROM stdin;
4	БТ-232049	Стопорный	32.000	0.180	3	490.000	89.000	63.000	\N	\N	2.000	\N
5	БТ-274875	Стопорный	36.000	0.248	3	513.000	89.000	68.000	\N	\N	2.000	\N
6	БТ-211918	Стопорный	36.000	0.280	3	468.000	89.000	73.000	\N	\N	2.000	\N
7	БТ-267171	Стопорный	38.000	0.280	3	159.900	90.000	50.500	\N	\N	1.600	\N
13	БТ-225400-01	Регулирующий	45.000	0.215	4	325.000	48.000	22.000	25.000	\N	5.000	\N
14	БТ-246490-01	Регулирующий	40.000	0.205	4	395.000	49.000	24.000	39.000	\N	2.000	\N
15	БТ-246490-02	Регулирующий	40.000	0.205	4	395.000	49.000	24.000	39.000	\N	2.000	\N
18	БТ-168560-1	Регулирующий	50.000	0.215	4	353.500	50.000	25.000	37.500	\N	2.000	\N
40	БТ-236455 (-1)	Стопорный	36.000	0.271	3	513.000	89.000	68.000	\N	\N	\N	\N
50	\N	Стопорный	80.000	0.233	3	110.000	110.000	77.500	\N	\N	\N	\N
55	БТ-281220, БТ-281222	Регулирующий	50.000	0.215	3	428.500	35.000	37.500	\N	\N	\N	\N
56	БТ-281225, БТ-281225-1	Регулирующий	42.000	0.215	3	507.000	40.000	\N	\N	\N	\N	\N
46	БТ-275666	Регулирующий	40.000	0.215	4	309.500	50.000	25.000	37.500	\N	\N	28
22	БТ-275666	Регулирующий	40.000	0.215	4	313.500	50.000	25.000	37.500	\N	2.000	28
39	БТ-285130	Стопорный	38.000	0.280	3	161.500	90.000	50.500	\N	\N	\N	20
38	БТ-284871	Регулирующий	40.000	0.215	4	299.500	50.000	25.000	37.500	\N	\N	20
45	БТ-281699	Стопорный	38.000	0.280	3	161.500	90.000	50.500	\N	\N	\N	27
8	БТ-281699	Стопорный	38.000	0.280	3	159.900	90.000	50.500	\N	\N	1.600	27
44	БТ-281695	Регулирующий	50.000	0.215	4	314.500	50.000	25.000	37.500	\N	\N	27
19	БТ-281695	Регулирующий	50.000	0.215	4	312.500	50.000	25.000	37.500	\N	2.000	27
57	БТ-281226	Регулирующий	\N	\N	\N	\N	\N	\N	\N	\N	\N	15
20	БТ-281220	Регулирующий	50.000	0.215	3	430.500	35.000	37.500	\N	\N	2.000	15
26	УТЗ-304414	Стопорный	36.000	0.271	3	513.000	89.000	68.000	\N	\N	\N	1
1	УТЗ-304414	Стопорный	36.000	0.271	3	513.000	89.000	68.000	\N	\N	2.000	1
27	БТ-225400	Регулирующий	45.000	0.215	4	290.000	48.000	25.000	25.000	\N	\N	1
12	БТ-225400	Регулирующий	45.000	0.215	4	325.000	48.000	22.000	25.000	\N	5.000	1
23	БТ-287950	Стопорный	36.000	0.271	3	513.000	89.000	68.000	\N	\N	2.000	7
24	БТ-288245	Стопорно-регулирующий	50.000	0.233	4	286.000	165.000	82.000	274.000	\N	\N	7
25	УТЗ-300805	Регулирующий	80.000	0.233	3	203.000	145.000	101.500	\N	\N	\N	7
2	БТ-236455	Стопорный	36.000	0.271	3	513.000	89.000	68.000	\N	\N	2.000	24
41	БТ-250791	Регулирующий	50.000	0.215	4	353.500	50.000	25.000	37.500	\N	\N	24
16	БТ-250791	Регулирующий	50.000	0.215	4	353.500	50.000	25.000	37.500	\N	2.000	24
42	БТ-250792	Регулирующий	36.000	0.205	4	438.500	50.000	25.000	37.500	\N	\N	24
21	БТ-250792	Регулирующий	36.000	0.205	4	438.500	50.000	25.000	37.500	\N	2.000	24
43	БТ-252380	Стопорный	36.000	0.271	3	513.000	89.000	68.000	\N	\N	\N	24
9	БТ-252380	Стопорный	36.000	0.271	3	513.000	89.000	68.000	\N	\N	2.000	24
54	БТ-262145-1	Регулирующий	40.000	0.215	4	299.500	50.000	25.000	37.500	\N	\N	10
52	БТ-274925	Регулирующий	40.000	0.215	4	319.500	50.000	25.000	37.500	\N	\N	21
17	БТ-274925	Регулирующий	40.000	0.215	4	319.500	50.000	25.000	37.500	\N	2.000	21
28	БТ-195900-3	Регулирующий	45.000	0.230	5	203.000	125.000	60.000	50.000	53.000	\N	26
29	БТ-195910-3	Регулирующий	45.000	0.110	5	296.000	125.000	60.000	50.000	53.000	\N	26
30	БТ-228380	Стопорный	32.000	0.290	4	415.000	78.000	55.000	43.000	\N	\N	26
33	УТЗ-306824	Стопорный	32.000	0.280	4	403.000	78.000	55.000	43.000	\N	\N	11
31	УТЗ-302063	Регулирующий	50.000	0.290	5	132.000	125.000	60.000	50.000	53.000	\N	11
32	УТЗ-302064	Стопорный	50.000	0.290	5	202.000	125.000	60.000	50.000	53.000	\N	11
36	БТ-273753	Стопорный	32.000	0.280	4	403.000	78.000	55.000	43.000	\N	\N	6
10	БТ-273753	Стопорный	32.000	0.280	4	403.000	78.000	55.000	43.000	\N	2.000	6
34	БТ-273755	Регулирующий	50.000	0.290	5	132.000	125.000	60.000	50.000	53.000	\N	6
35	БТ-273756	Регулирующий	50.000	0.290	5	202.000	125.000	60.000	50.000	53.000	\N	6
53	УТЗ-308701	Стопорный	36.000	0.271	3	513.000	89.000	68.000	\N	\N	\N	12
37	БТ-232049-1	Стопорный	32.000	0.180	3	490.000	89.000	63.000	\N	\N	\N	25
3	БТ-232049-1	Стопорный	32.000	0.180	3	490.000	89.000	63.000	\N	\N	2.000	25
48	БТ-271369	Регулирующий	45.000	0.215	4	336.500	50.000	25.000	37.500	\N	\N	5
51	БТ-267171-1	Стопорный	38.000	0.280	3	161.500	90.000	50.500	\N	\N	\N	31
11	БТ-267171-1	Стопорный	38.000	0.280	3	161.500	102.500	50.500	\N	\N	2.000	31
49	БТ-269982	Стопорно-регулирующий	50.000	0.230	3	187.500	110.000	292.500	\N	\N	\N	31
47	БТ-280544	Регулирующий	50.000	0.215	4	509.500	50.000	25.000	37.500	\N	\N	9
\.


--
-- TOC entry 4814 (class 0 OID 24800)
-- Dependencies: 220
-- Data for Name: turbines; Type: TABLE DATA; Schema: autocalc; Owner: postgres
--

COPY autocalc.turbines (id, name, valves) FROM stdin;
1	К-17-1,6	БТ-255031
2	К-17-1,6	БТ-255031
3	К-63-90	БТ-271614
4	К-63-90	БТ-271614
5	К-65-12,8	БТ-275666
6	К-85-8,0	БТ-285130
7	К-85-8,0	БТ-284871
8	К-85-8,0	БТ-285130
9	К-85-8,0	БТ-284871
10	Кп-77-6,8	БТ-281699
11	Кп-77-6,8	БТ-281695
12	ПТ-100/110-12,8/1,3	БТ-281226
13	ПТ-100/110-12,8/1,3	БТ-280760
14	ПТ-100/110-12,8/1,3	БТ-280760
15	ПТ-100/110-12,8/1,3	БТ-281220
16	ПТ-100/110-12,8/1,3	БТ-281222
17	ПТ-100/110-12,8/1,3	БТ-281225
18	ПТ-100/110-12,8/1,3	БТ-281225-1
19	ПТ-135, Т-185	УТЗ-304414
20	ПТ-135, Т-185	БТ-225400
21	ПТ-135/165-130/15	БТ-206497
22	ПТ-135/165-130/15	БТ-206497
23	ПТ-150	БТ-287950
24	ПТ-150	БТ-288245
25	ПТ-150	УТЗ-300805
26	ПТ-30/35-90/10-5	БТ-252202
27	ПТ-30/35-90/10-5	БТ-252202
28	ПТ-50-130/7	БТ-157560
29	ПТ-50-130/7	БТ-157560
30	ПТ-65-12,8/1,3	УТЗ-300104
31	ПТ-65-12,8/1,3	УТЗ-300104
32	ПТ-90/125-130-2	БТ-253490
33	ПТ-90/125-130-2	БТ-253490
34	Р-38-130/34 ПР1	БТ-236626-02
35	Р-38-130/34 ПР1	БТ-236626-02
36	Т-100/120-130-3	БТ-216362
37	Т-100/120-130-3	БТ-216362
38	Т-110	БТ-236455-1
39	Т-110	БТ-236455
40	Т-110	БТ-250791
41	Т-110	БТ-250792
42	Т-110	БТ-252380
43	Т-110/120-130-5	БТ-236626
44	Т-110/120-130-5	БТ-236626
45	Т-110/120-130-5В	БТ-252375
46	Т-110/120-130-5В	БТ-252375
47	Т-113/145-12,4	БТ-262145-1
48	Т-125/150-12,8	БТ-274925
49	Т-175/210-130	БТ-218771
50	Т-175/210-130	БТ-218771
51	Т-250	БТ-195900-3
52	Т-250	БТ-195910-3
53	Т-250	БТ-228380
54	Т-250/300-240	БТ-197700
55	Т-250/300-240	БТ-197700
56	Т-259	УТЗ-306824
57	Т-259	УТЗ-302063
58	Т-259	УТЗ-302064
59	Т-260/300-240	БТ-235893
60	Т-260/300-240	БТ-235893
61	Т-295	БТ-273753
62	Т-295	БТ-273755
63	Т-295	БТ-273756
64	Т-295/335-23,5	БТ-235893-01
65	Т-295/335-23,5	БТ-235893-01
66	Т-50-130-1	УТЗ-308701
67	Т-50/60-8,8	БТ-232049-1
68	Т-60/65-8,8	БТ-271369
69	Т-63/76-8,8	БТ-269095
70	Т-63/76-8,8	БТ-270300
71	Т-63/76-8,8	БТ-270300
72	Т-63/76-8,8	БТ-267171-1
73	Т-63/76-8,8	БТ-269982
74	Т-63/76-8,8	БТ-269095
75	Тп-115/130-12,8	БТ-280544
76	ТР-110-130	БТ-236626-01
77	ТР-110-130	БТ-236626-01
\.


--
-- TOC entry 4817 (class 0 OID 24819)
-- Dependencies: 223
-- Data for Name: unique_turbine; Type: TABLE DATA; Schema: autocalc; Owner: postgres
--

COPY autocalc.unique_turbine (id, name) FROM stdin;
1	ПТ-135, Т-185
2	Т-110/120-130-5
3	ПТ-135/165-130/15
4	Р-38-130/34 ПР1
5	Т-60/65-8,8
6	Т-295
7	ПТ-150
8	Т-260/300-240
9	Тп-115/130-12,8
10	Т-113/145-12,4
11	Т-259
12	Т-50-130-1
13	Т-110/120-130-5В
14	ПТ-90/125-130-2
15	ПТ-100/110-12,8/1,3
16	Т-295/335-23,5
17	ПТ-30/35-90/10-5
18	ТР-110-130
19	Т-175/210-130
20	К-85-8,0
21	Т-125/150-12,8
22	Т-100/120-130-3
23	Т-250/300-240
24	Т-110
25	Т-50/60-8,8
26	Т-250
27	Кп-77-6,8
28	К-65-12,8
29	ПТ-65-12,8/1,3
30	К-63-90
31	Т-63/76-8,8
32	ПТ-50-130/7
33	К-17-1,6
\.


--
-- TOC entry 4828 (class 0 OID 0)
-- Dependencies: 217
-- Name: resultcalcs_id_seq; Type: SEQUENCE SET; Schema: autocalc; Owner: postgres
--

SELECT pg_catalog.setval('autocalc.resultcalcs_id_seq', 1, false);


--
-- TOC entry 4829 (class 0 OID 0)
-- Dependencies: 219
-- Name: stocks_id_seq; Type: SEQUENCE SET; Schema: autocalc; Owner: postgres
--

SELECT pg_catalog.setval('autocalc.stocks_id_seq', 57, true);


--
-- TOC entry 4830 (class 0 OID 0)
-- Dependencies: 221
-- Name: turbines_id_seq; Type: SEQUENCE SET; Schema: autocalc; Owner: postgres
--

SELECT pg_catalog.setval('autocalc.turbines_id_seq', 1, false);


--
-- TOC entry 4831 (class 0 OID 0)
-- Dependencies: 222
-- Name: unique_turbine_id_seq; Type: SEQUENCE SET; Schema: autocalc; Owner: postgres
--

SELECT pg_catalog.setval('autocalc.unique_turbine_id_seq', 33, true);


--
-- TOC entry 4656 (class 2606 OID 24808)
-- Name: resultcalcs resultcalcs_pkey; Type: CONSTRAINT; Schema: autocalc; Owner: postgres
--

ALTER TABLE ONLY autocalc.resultcalcs
    ADD CONSTRAINT resultcalcs_pkey PRIMARY KEY (id);


--
-- TOC entry 4658 (class 2606 OID 24810)
-- Name: stocks stocks_pkey; Type: CONSTRAINT; Schema: autocalc; Owner: postgres
--

ALTER TABLE ONLY autocalc.stocks
    ADD CONSTRAINT stocks_pkey PRIMARY KEY (id);


--
-- TOC entry 4660 (class 2606 OID 24812)
-- Name: turbines turbines_pkey; Type: CONSTRAINT; Schema: autocalc; Owner: postgres
--

ALTER TABLE ONLY autocalc.turbines
    ADD CONSTRAINT turbines_pkey PRIMARY KEY (id);


--
-- TOC entry 4662 (class 2606 OID 24826)
-- Name: unique_turbine unique_turbine_name_key; Type: CONSTRAINT; Schema: autocalc; Owner: postgres
--

ALTER TABLE ONLY autocalc.unique_turbine
    ADD CONSTRAINT unique_turbine_name_key UNIQUE (name);


--
-- TOC entry 4664 (class 2606 OID 24824)
-- Name: unique_turbine unique_turbine_pkey; Type: CONSTRAINT; Schema: autocalc; Owner: postgres
--

ALTER TABLE ONLY autocalc.unique_turbine
    ADD CONSTRAINT unique_turbine_pkey PRIMARY KEY (id);


--
-- TOC entry 4665 (class 2606 OID 24847)
-- Name: resultcalcs resultcalcs_valve_id_fkey; Type: FK CONSTRAINT; Schema: autocalc; Owner: postgres
--

ALTER TABLE ONLY autocalc.resultcalcs
    ADD CONSTRAINT resultcalcs_valve_id_fkey FOREIGN KEY (valve_id) REFERENCES autocalc.stocks(id);


--
-- TOC entry 4666 (class 2606 OID 24842)
-- Name: stocks stocks_turbine_id_fkey; Type: FK CONSTRAINT; Schema: autocalc; Owner: postgres
--

ALTER TABLE ONLY autocalc.stocks
    ADD CONSTRAINT stocks_turbine_id_fkey FOREIGN KEY (turbine_id) REFERENCES autocalc.unique_turbine(id);


-- Completed on 2024-10-25 22:14:24

--
-- PostgreSQL database dump complete
--

-- Completed on 2024-10-25 22:14:24

--
-- PostgreSQL database cluster dump complete
--

