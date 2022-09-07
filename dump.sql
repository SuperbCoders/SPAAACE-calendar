--
-- PostgreSQL database dump
--

-- Dumped from database version 14.3
-- Dumped by pg_dump version 14.3

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
-- Name: generate_code(); Type: FUNCTION; Schema: public; Owner: admin
--

CREATE FUNCTION public.generate_code() RETURNS text
    LANGUAGE sql
    AS $$
    SELECT array_to_string(array(select substr('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',((random()*(36-1)+1)::integer),1) from generate_series(1,16)),'');;
$$;


ALTER FUNCTION public.generate_code() OWNER TO admin;

--
-- Name: generate_id(); Type: FUNCTION; Schema: public; Owner: admin
--

CREATE FUNCTION public.generate_id() RETURNS text
    LANGUAGE sql
    AS $$
    SELECT array_to_string(array(select substr('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',((random()*(36-1)+1)::integer),1) from generate_series(1,6)),'');;
$$;


ALTER FUNCTION public.generate_id() OWNER TO admin;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: access; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.access (
    code text DEFAULT public.generate_code() NOT NULL
);


ALTER TABLE public.access OWNER TO admin;

--
-- Name: booking; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.booking (
    id text DEFAULT public.generate_id() NOT NULL,
    working_id text NOT NULL,
    start time without time zone DEFAULT LOCALTIME(0) NOT NULL,
    finish time without time zone DEFAULT LOCALTIME(0) NOT NULL,
    note text DEFAULT ''::text NOT NULL,
    name text NOT NULL,
    email text NOT NULL
);


ALTER TABLE public.booking OWNER TO admin;

--
-- Name: booking_products; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.booking_products (
    booking_id text NOT NULL,
    product_id text NOT NULL
);


ALTER TABLE public.booking_products OWNER TO admin;

--
-- Name: products; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.products (
    id text DEFAULT public.generate_id() NOT NULL,
    name text NOT NULL
);


ALTER TABLE public.products OWNER TO admin;

--
-- Name: working; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.working (
    id text DEFAULT public.generate_id() NOT NULL,
    start time without time zone DEFAULT LOCALTIME(0) NOT NULL,
    finish time without time zone DEFAULT LOCALTIME(0) NOT NULL,
    date date DEFAULT (now())::date NOT NULL
);


ALTER TABLE public.working OWNER TO admin;

--
-- Data for Name: access; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.access (code) FROM stdin;
A2R4CVZII3O0K256
\.


--
-- Data for Name: booking; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.booking (id, working_id, start, finish, note, name, email) FROM stdin;
\.


--
-- Data for Name: booking_products; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.booking_products (booking_id, product_id) FROM stdin;
\.


--
-- Data for Name: products; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.products (id, name) FROM stdin;
\.


--
-- Data for Name: working; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.working (id, start, finish, date) FROM stdin;
\.


--
-- Name: access access_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.access
    ADD CONSTRAINT access_pkey PRIMARY KEY (code);


--
-- Name: booking booking_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.booking
    ADD CONSTRAINT booking_pkey PRIMARY KEY (id);


--
-- Name: products products_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (id);


--
-- Name: working working_date_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.working
    ADD CONSTRAINT working_date_key UNIQUE (date);


--
-- Name: working working_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.working
    ADD CONSTRAINT working_pkey PRIMARY KEY (id);


--
-- Name: booking_products booking_products_booking_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.booking_products
    ADD CONSTRAINT booking_products_booking_id_fkey FOREIGN KEY (booking_id) REFERENCES public.booking(id) ON DELETE CASCADE;


--
-- Name: booking_products booking_products_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.booking_products
    ADD CONSTRAINT booking_products_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE CASCADE;


--
-- Name: booking booking_working_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.booking
    ADD CONSTRAINT booking_working_id_fkey FOREIGN KEY (working_id) REFERENCES public.working(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

