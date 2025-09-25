--
-- PostgreSQL database dump
--

\restrict IiXr59D4RPphNSd6DitSZtJFZFyfsqhNk3FHs53EWv56A2ywfvf1WGQHxx1Gmp8

-- Dumped from database version 16.10 (Debian 16.10-1.pgdg13+1)
-- Dumped by pg_dump version 16.10 (Ubuntu 16.10-0ubuntu0.24.04.1)

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
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: app_screen_audios_screenname_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.app_screen_audios_screenname_enum AS ENUM (
    'WelcomeLanguageScreen',
    'WelcomeSigninScreen',
    'RegistrationPhoneNumberScreen',
    'RegistrationVerificationCodeScreen',
    'RegistrationUploadIdScreen',
    'RegistrationIdPreambleScreen',
    'RegistrationSelfieScreen',
    'RegistrationSelfiePreambleScreen',
    'RegistrationGoalsScreen',
    'RegistrationRecommendedAppsScreen',
    'RegistrationPinSetupScreen',
    'HomeGoalsScreen',
    'HomeMessagesScreen',
    'HomeProfileScreen',
    'HomeSupportScreen',
    'HomeRecommendationsScreen',
    'PermissionsModal'
);


ALTER TYPE public.app_screen_audios_screenname_enum OWNER TO postgres;

--
-- Name: messages_status_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.messages_status_enum AS ENUM (
    'draft',
    'published'
);


ALTER TYPE public.messages_status_enum OWNER TO postgres;

--
-- Name: messages_type_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.messages_type_enum AS ENUM (
    'system',
    'coach'
);


ALTER TYPE public.messages_type_enum OWNER TO postgres;

--
-- Name: user_goal_categories_relationshiptype_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.user_goal_categories_relationshiptype_enum AS ENUM (
    'primary',
    'secondary',
    'tertiary'
);


ALTER TYPE public.user_goal_categories_relationshiptype_enum OWNER TO postgres;

--
-- Name: user_goals_relationshiptype_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.user_goals_relationshiptype_enum AS ENUM (
    'primary',
    'secondary',
    'tertiary'
);


ALTER TYPE public.user_goals_relationshiptype_enum OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: admin_users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.admin_users (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "createdAt" timestamp without time zone DEFAULT now() NOT NULL,
    "updatedAt" timestamp without time zone DEFAULT now() NOT NULL,
    email character varying NOT NULL,
    name character varying NOT NULL,
    password character varying NOT NULL,
    "isActive" boolean DEFAULT true NOT NULL,
    role character varying DEFAULT 'admin'::character varying NOT NULL
);


ALTER TABLE public.admin_users OWNER TO postgres;

--
-- Name: app_audios; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.app_audios (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "createdAt" timestamp without time zone DEFAULT now() NOT NULL,
    "updatedAt" timestamp without time zone DEFAULT now() NOT NULL,
    "appId" uuid NOT NULL,
    "languageCode" character varying NOT NULL,
    "fileUrl" character varying NOT NULL
);


ALTER TABLE public.app_audios OWNER TO postgres;

--
-- Name: app_goal_sub_categories; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.app_goal_sub_categories (
    "appsId" uuid NOT NULL,
    "goalSubCategoriesId" uuid NOT NULL
);


ALTER TABLE public.app_goal_sub_categories OWNER TO postgres;

--
-- Name: app_goals; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.app_goals (
    "appsId" uuid NOT NULL,
    "goalsId" uuid NOT NULL
);


ALTER TABLE public.app_goals OWNER TO postgres;

--
-- Name: app_screen_audios; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.app_screen_audios (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "screenName" public.app_screen_audios_screenname_enum NOT NULL,
    "languageCode" character varying(10) NOT NULL,
    "audioUrl" text NOT NULL,
    duration integer,
    "createdAt" timestamp without time zone DEFAULT now() NOT NULL,
    "updatedAt" timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.app_screen_audios OWNER TO postgres;

--
-- Name: apps; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.apps (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "createdAt" timestamp without time zone DEFAULT now() NOT NULL,
    "updatedAt" timestamp without time zone DEFAULT now() NOT NULL,
    title character varying NOT NULL,
    description character varying,
    "imageUrl" character varying,
    "appId" character varying NOT NULL,
    "countryCode" character varying,
    "goalCategoryId" uuid
);


ALTER TABLE public.apps OWNER TO postgres;

--
-- Name: countries; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.countries (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "createdAt" timestamp without time zone DEFAULT now() NOT NULL,
    "updatedAt" timestamp without time zone DEFAULT now() NOT NULL,
    code character varying(2) NOT NULL,
    name character varying NOT NULL,
    "flagUrl" character varying
);


ALTER TABLE public.countries OWNER TO postgres;

--
-- Name: country_languages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.country_languages (
    "countriesId" uuid NOT NULL,
    "languagesId" uuid NOT NULL
);


ALTER TABLE public.country_languages OWNER TO postgres;

--
-- Name: events; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.events (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    event_type character varying(100) NOT NULL,
    "timestamp" bigint NOT NULL,
    data jsonb NOT NULL,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.events OWNER TO postgres;

--
-- Name: goal_categories; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.goal_categories (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "createdAt" timestamp without time zone DEFAULT now() NOT NULL,
    "updatedAt" timestamp without time zone DEFAULT now() NOT NULL,
    name character varying NOT NULL,
    description character varying,
    "iconUrl" character varying,
    "order" integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.goal_categories OWNER TO postgres;

--
-- Name: goal_priorities; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.goal_priorities (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "createdAt" timestamp without time zone DEFAULT now() NOT NULL,
    "updatedAt" timestamp without time zone DEFAULT now() NOT NULL,
    title character varying NOT NULL,
    "goalCategoryId" uuid NOT NULL
);


ALTER TABLE public.goal_priorities OWNER TO postgres;

--
-- Name: goal_sub_categories; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.goal_sub_categories (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "createdAt" timestamp without time zone DEFAULT now() NOT NULL,
    "updatedAt" timestamp without time zone DEFAULT now() NOT NULL,
    name character varying NOT NULL,
    description character varying,
    "goalCategoryId" uuid NOT NULL
);


ALTER TABLE public.goal_sub_categories OWNER TO postgres;

--
-- Name: goals; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.goals (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "createdAt" timestamp without time zone DEFAULT now() NOT NULL,
    "updatedAt" timestamp without time zone DEFAULT now() NOT NULL,
    title character varying NOT NULL,
    "displayText" character varying,
    "goalCategoryId" uuid NOT NULL,
    "goalSubCategoryId" uuid
);


ALTER TABLE public.goals OWNER TO postgres;

--
-- Name: high_watermarks; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.high_watermarks (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    source character varying(100) NOT NULL,
    last_processed_key character varying(500),
    last_processed_timestamp timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.high_watermarks OWNER TO postgres;

--
-- Name: interventions_log; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.interventions_log (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    intervention_id character varying(100) NOT NULL,
    context jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    decided_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.interventions_log OWNER TO postgres;

--
-- Name: languages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.languages (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "createdAt" timestamp without time zone DEFAULT now() NOT NULL,
    "updatedAt" timestamp without time zone DEFAULT now() NOT NULL,
    title character varying NOT NULL,
    code character varying NOT NULL
);


ALTER TABLE public.languages OWNER TO postgres;

--
-- Name: message_templates; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.message_templates (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "createdAt" timestamp without time zone DEFAULT now() NOT NULL,
    "updatedAt" timestamp without time zone DEFAULT now() NOT NULL,
    title character varying NOT NULL,
    subject character varying NOT NULL,
    content text NOT NULL,
    category character varying,
    translations jsonb,
    "subjectTranslations" jsonb,
    "isActive" boolean DEFAULT true NOT NULL,
    "videoUrls" jsonb,
    "audioUrls" jsonb
);


ALTER TABLE public.message_templates OWNER TO postgres;

--
-- Name: messages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.messages (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "createdAt" timestamp without time zone DEFAULT now() NOT NULL,
    "updatedAt" timestamp without time zone DEFAULT now() NOT NULL,
    subject character varying NOT NULL,
    text character varying NOT NULL,
    "from" character varying NOT NULL,
    type public.messages_type_enum DEFAULT 'system'::public.messages_type_enum NOT NULL,
    "videoUrl" character varying,
    "audioUrl" character varying,
    "coachId" uuid,
    "userIds" text,
    status public.messages_status_enum DEFAULT 'draft'::public.messages_status_enum NOT NULL
);


ALTER TABLE public.messages OWNER TO postgres;

--
-- Name: rewards_issued; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.rewards_issued (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    reward_id character varying(100) NOT NULL,
    amount numeric(10,2),
    unit character varying(20),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.rewards_issued OWNER TO postgres;

--
-- Name: services; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.services (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "createdAt" timestamp without time zone DEFAULT now() NOT NULL,
    "updatedAt" timestamp without time zone DEFAULT now() NOT NULL,
    title character varying NOT NULL,
    description character varying,
    "goalSubCategoryId" character varying NOT NULL
);


ALTER TABLE public.services OWNER TO postgres;

--
-- Name: user_apps; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_apps (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "createdAt" timestamp without time zone DEFAULT now() NOT NULL,
    "updatedAt" timestamp without time zone DEFAULT now() NOT NULL,
    "appId" uuid NOT NULL,
    "isFavorite" boolean DEFAULT false NOT NULL,
    "usageCount" integer DEFAULT 0 NOT NULL,
    "userId" uuid NOT NULL
);


ALTER TABLE public.user_apps OWNER TO postgres;

--
-- Name: user_engagement_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_engagement_logs (
    id uuid NOT NULL,
    user_id character varying(255) NOT NULL,
    data_type character varying(50) NOT NULL,
    "timestamp" bigint NOT NULL,
    data jsonb,
    signal_name character varying(255),
    signal_value numeric,
    signal_metadata jsonb,
    milestone_name character varying(255),
    milestone_status character varying(50),
    milestone_timestamp bigint,
    milestone_metadata jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.user_engagement_logs OWNER TO postgres;

--
-- Name: user_goal_categories; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_goal_categories (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "createdAt" timestamp without time zone DEFAULT now() NOT NULL,
    "updatedAt" timestamp without time zone DEFAULT now() NOT NULL,
    "relationshipType" public.user_goal_categories_relationshiptype_enum DEFAULT 'primary'::public.user_goal_categories_relationshiptype_enum NOT NULL,
    "goalCategoryId" uuid NOT NULL,
    "userId" uuid NOT NULL,
    rank integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.user_goal_categories OWNER TO postgres;

--
-- Name: user_goal_priorities; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_goal_priorities (
    "userGoalCategoryId" uuid NOT NULL,
    "goalPriorityId" uuid NOT NULL
);


ALTER TABLE public.user_goal_priorities OWNER TO postgres;

--
-- Name: user_goals; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_goals (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "createdAt" timestamp without time zone DEFAULT now() NOT NULL,
    "updatedAt" timestamp without time zone DEFAULT now() NOT NULL,
    "relationshipType" public.user_goals_relationshiptype_enum DEFAULT 'primary'::public.user_goals_relationshiptype_enum NOT NULL,
    "goalId" uuid,
    "userId" uuid NOT NULL
);


ALTER TABLE public.user_goals OWNER TO postgres;

--
-- Name: user_messages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_messages (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "createdAt" timestamp without time zone DEFAULT now() NOT NULL,
    "updatedAt" timestamp without time zone DEFAULT now() NOT NULL,
    "messageId" uuid NOT NULL,
    "isRead" boolean DEFAULT false NOT NULL,
    "viewedAt" timestamp without time zone,
    "userId" uuid NOT NULL
);


ALTER TABLE public.user_messages OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    "createdAt" timestamp without time zone DEFAULT now() NOT NULL,
    "updatedAt" timestamp without time zone DEFAULT now() NOT NULL,
    "phoneNumber" character varying NOT NULL,
    email character varying,
    name character varying,
    password character varying,
    "isVerified" boolean DEFAULT false NOT NULL,
    "profilePicture" character varying,
    "countryCode" character varying,
    "idNumber" character varying,
    gender character varying,
    birthdate date,
    address character varying,
    "expiryDate" date,
    "imageFront" character varying,
    "imageBack" character varying,
    "selfieImage" character varying,
    "mailId" character varying,
    pin character varying,
    "countryId" uuid,
    "primaryLanguageId" uuid,
    "secondaryLanguageId" uuid,
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: verifications; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.verifications (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    "createdAt" timestamp without time zone DEFAULT now() NOT NULL,
    "updatedAt" timestamp without time zone DEFAULT now() NOT NULL,
    "phoneNumber" character varying NOT NULL,
    code character varying NOT NULL,
    verified boolean DEFAULT false NOT NULL,
    "expiresAt" timestamp without time zone NOT NULL
);


ALTER TABLE public.verifications OWNER TO postgres;

--
-- Name: app_goal_sub_categories PK_04c0eeefd08feba8dca1c4a64ff; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.app_goal_sub_categories
    ADD CONSTRAINT "PK_04c0eeefd08feba8dca1c4a64ff" PRIMARY KEY ("appsId", "goalSubCategoriesId");


--
-- Name: admin_users PK_06744d221bb6145dc61e5dc441d; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admin_users
    ADD CONSTRAINT "PK_06744d221bb6145dc61e5dc441d" PRIMARY KEY (id);


--
-- Name: messages PK_18325f38ae6de43878487eff986; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT "PK_18325f38ae6de43878487eff986" PRIMARY KEY (id);


--
-- Name: goal_categories PK_1c80eac47901d682e6d5fcea6e2; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.goal_categories
    ADD CONSTRAINT "PK_1c80eac47901d682e6d5fcea6e2" PRIMARY KEY (id);


--
-- Name: user_goals PK_1cf8a9384f9f60fef678fd8f363; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_goals
    ADD CONSTRAINT "PK_1cf8a9384f9f60fef678fd8f363" PRIMARY KEY (id);


--
-- Name: verifications PK_2127ad1b143cf012280390b01d1; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.verifications
    ADD CONSTRAINT "PK_2127ad1b143cf012280390b01d1" PRIMARY KEY (id);


--
-- Name: goals PK_26e17b251afab35580dff769223; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.goals
    ADD CONSTRAINT "PK_26e17b251afab35580dff769223" PRIMARY KEY (id);


--
-- Name: goal_priorities PK_2744fcba44fa4aa87dc905bb0cb; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.goal_priorities
    ADD CONSTRAINT "PK_2744fcba44fa4aa87dc905bb0cb" PRIMARY KEY (id);


--
-- Name: user_goal_priorities PK_30467a2d9c540f576a573fc857e; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_goal_priorities
    ADD CONSTRAINT "PK_30467a2d9c540f576a573fc857e" PRIMARY KEY ("userGoalCategoryId", "goalPriorityId");


--
-- Name: country_languages PK_38ac9ad6f634d8d25a121a37a01; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.country_languages
    ADD CONSTRAINT "PK_38ac9ad6f634d8d25a121a37a01" PRIMARY KEY ("countriesId", "languagesId");


--
-- Name: app_screen_audios PK_3957709131229cca533a8737464; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.app_screen_audios
    ADD CONSTRAINT "PK_3957709131229cca533a8737464" PRIMARY KEY (id);


--
-- Name: user_goal_categories PK_5731001bd11205105ee1b12911c; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_goal_categories
    ADD CONSTRAINT "PK_5731001bd11205105ee1b12911c" PRIMARY KEY (id);


--
-- Name: user_messages PK_5a90e206d5e3dfde48f640ea7c6; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_messages
    ADD CONSTRAINT "PK_5a90e206d5e3dfde48f640ea7c6" PRIMARY KEY (id);


--
-- Name: message_templates PK_9ac2bd9635be662d183f314947d; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.message_templates
    ADD CONSTRAINT "PK_9ac2bd9635be662d183f314947d" PRIMARY KEY (id);


--
-- Name: app_goals PK_9cc7a93ee691384dc0b4feefc62; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.app_goals
    ADD CONSTRAINT "PK_9cc7a93ee691384dc0b4feefc62" PRIMARY KEY ("appsId", "goalsId");


--
-- Name: users PK_a3ffb1c0c8416b9fc6f907b7433; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT "PK_a3ffb1c0c8416b9fc6f907b7433" PRIMARY KEY (id);


--
-- Name: countries PK_b2d7006793e8697ab3ae2deff18; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.countries
    ADD CONSTRAINT "PK_b2d7006793e8697ab3ae2deff18" PRIMARY KEY (id);


--
-- Name: languages PK_b517f827ca496b29f4d549c631d; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.languages
    ADD CONSTRAINT "PK_b517f827ca496b29f4d549c631d" PRIMARY KEY (id);


--
-- Name: services PK_ba2d347a3168a296416c6c5ccb2; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.services
    ADD CONSTRAINT "PK_ba2d347a3168a296416c6c5ccb2" PRIMARY KEY (id);


--
-- Name: apps PK_c5121fda0f8268f1f7f84134e19; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.apps
    ADD CONSTRAINT "PK_c5121fda0f8268f1f7f84134e19" PRIMARY KEY (id);


--
-- Name: app_audios PK_e07326acdd3c4997631419bb2e3; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.app_audios
    ADD CONSTRAINT "PK_e07326acdd3c4997631419bb2e3" PRIMARY KEY (id);


--
-- Name: goal_sub_categories PK_e9a62f07690b0ffff7b9c478c44; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.goal_sub_categories
    ADD CONSTRAINT "PK_e9a62f07690b0ffff7b9c478c44" PRIMARY KEY (id);


--
-- Name: user_apps PK_fc0f4f1c464efb7357f6869c15c; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_apps
    ADD CONSTRAINT "PK_fc0f4f1c464efb7357f6869c15c" PRIMARY KEY (id);


--
-- Name: languages UQ_06df62e773ec68318919dafacf7; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.languages
    ADD CONSTRAINT "UQ_06df62e773ec68318919dafacf7" UNIQUE (title);


--
-- Name: users UQ_1e3d0240b49c40521aaeb953293; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT "UQ_1e3d0240b49c40521aaeb953293" UNIQUE ("phoneNumber");


--
-- Name: languages UQ_7397752718d1c9eb873722ec9b2; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.languages
    ADD CONSTRAINT "UQ_7397752718d1c9eb873722ec9b2" UNIQUE (code);


--
-- Name: apps UQ_88d9328b5403a89eb94af4d5653; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.apps
    ADD CONSTRAINT "UQ_88d9328b5403a89eb94af4d5653" UNIQUE ("appId");


--
-- Name: goals UQ_960318654fa170aae9a3f9e7a40; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.goals
    ADD CONSTRAINT "UQ_960318654fa170aae9a3f9e7a40" UNIQUE (title);


--
-- Name: countries UQ_b47cbb5311bad9c9ae17b8c1eda; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.countries
    ADD CONSTRAINT "UQ_b47cbb5311bad9c9ae17b8c1eda" UNIQUE (code);


--
-- Name: goal_categories UQ_c2d9668747087ca1017e1846ce7; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.goal_categories
    ADD CONSTRAINT "UQ_c2d9668747087ca1017e1846ce7" UNIQUE (name);


--
-- Name: goal_sub_categories UQ_c4bd943fc2c32c451e00db6325d; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.goal_sub_categories
    ADD CONSTRAINT "UQ_c4bd943fc2c32c451e00db6325d" UNIQUE (name);


--
-- Name: admin_users UQ_dcd0c8a4b10af9c986e510b9ecc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admin_users
    ADD CONSTRAINT "UQ_dcd0c8a4b10af9c986e510b9ecc" UNIQUE (email);


--
-- Name: events events_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_pkey PRIMARY KEY (id);


--
-- Name: high_watermarks high_watermarks_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.high_watermarks
    ADD CONSTRAINT high_watermarks_pkey PRIMARY KEY (id);


--
-- Name: interventions_log interventions_log_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.interventions_log
    ADD CONSTRAINT interventions_log_pkey PRIMARY KEY (id);


--
-- Name: rewards_issued rewards_issued_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rewards_issued
    ADD CONSTRAINT rewards_issued_pkey PRIMARY KEY (id);


--
-- Name: user_engagement_logs user_engagement_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_engagement_logs
    ADD CONSTRAINT user_engagement_logs_pkey PRIMARY KEY (id);


--
-- Name: IDX_0c4cce5a5fac446cf045fc0a0a; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "IDX_0c4cce5a5fac446cf045fc0a0a" ON public.app_goal_sub_categories USING btree ("goalSubCategoriesId");


--
-- Name: IDX_285c3533ad0e71168f015c71dd; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "IDX_285c3533ad0e71168f015c71dd" ON public.app_goal_sub_categories USING btree ("appsId");


--
-- Name: IDX_58b864fe2d90186e32372df25a; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "IDX_58b864fe2d90186e32372df25a" ON public.app_goals USING btree ("appsId");


--
-- Name: IDX_5bbf8c7905218e8daf83734ecc; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "IDX_5bbf8c7905218e8daf83734ecc" ON public.user_goal_priorities USING btree ("userGoalCategoryId");


--
-- Name: IDX_89dc703d8ca945151a4fb0945c; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "IDX_89dc703d8ca945151a4fb0945c" ON public.country_languages USING btree ("countriesId");


--
-- Name: IDX_b321147e5c326be40fc9c68c51; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "IDX_b321147e5c326be40fc9c68c51" ON public.country_languages USING btree ("languagesId");


--
-- Name: IDX_bba7a20d94bd8e16204a2bb6b9; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "IDX_bba7a20d94bd8e16204a2bb6b9" ON public.user_goal_priorities USING btree ("goalPriorityId");


--
-- Name: IDX_f5217329c699f0327b2d9cb9c2; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "IDX_f5217329c699f0327b2d9cb9c2" ON public.app_goals USING btree ("goalsId");


--
-- Name: idx_user_engagement_logs_data_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_user_engagement_logs_data_type ON public.user_engagement_logs USING btree (data_type);


--
-- Name: idx_user_engagement_logs_timestamp; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_user_engagement_logs_timestamp ON public.user_engagement_logs USING btree ("timestamp");


--
-- Name: idx_user_engagement_logs_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_user_engagement_logs_user_id ON public.user_engagement_logs USING btree (user_id);


--
-- Name: goals FK_08e63ee409a979262dc1d1868b6; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.goals
    ADD CONSTRAINT "FK_08e63ee409a979262dc1d1868b6" FOREIGN KEY ("goalSubCategoryId") REFERENCES public.goal_sub_categories(id);


--
-- Name: app_goal_sub_categories FK_0c4cce5a5fac446cf045fc0a0a4; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.app_goal_sub_categories
    ADD CONSTRAINT "FK_0c4cce5a5fac446cf045fc0a0a4" FOREIGN KEY ("goalSubCategoriesId") REFERENCES public.goal_sub_categories(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: app_goal_sub_categories FK_285c3533ad0e71168f015c71dd5; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.app_goal_sub_categories
    ADD CONSTRAINT "FK_285c3533ad0e71168f015c71dd5" FOREIGN KEY ("appsId") REFERENCES public.apps(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: user_goals FK_4bbd0401b703af6edaa27ea4cf6; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_goals
    ADD CONSTRAINT "FK_4bbd0401b703af6edaa27ea4cf6" FOREIGN KEY ("goalId") REFERENCES public.goals(id);


--
-- Name: app_goals FK_58b864fe2d90186e32372df25a6; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.app_goals
    ADD CONSTRAINT "FK_58b864fe2d90186e32372df25a6" FOREIGN KEY ("appsId") REFERENCES public.apps(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: user_goal_priorities FK_5bbf8c7905218e8daf83734ecc9; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_goal_priorities
    ADD CONSTRAINT "FK_5bbf8c7905218e8daf83734ecc9" FOREIGN KEY ("userGoalCategoryId") REFERENCES public.user_goal_categories(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: user_messages FK_68d799aeb820f0e823c1120fe73; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_messages
    ADD CONSTRAINT "FK_68d799aeb820f0e823c1120fe73" FOREIGN KEY ("userId") REFERENCES public.users(id);


--
-- Name: goal_sub_categories FK_72d89d705970ac523386529c698; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.goal_sub_categories
    ADD CONSTRAINT "FK_72d89d705970ac523386529c698" FOREIGN KEY ("goalCategoryId") REFERENCES public.goal_categories(id);


--
-- Name: app_audios FK_7ae4353751bb071391a40fcb195; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.app_audios
    ADD CONSTRAINT "FK_7ae4353751bb071391a40fcb195" FOREIGN KEY ("appId") REFERENCES public.apps(id) ON DELETE CASCADE;


--
-- Name: user_goal_categories FK_8001bb6194cd9ad717606002b20; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_goal_categories
    ADD CONSTRAINT "FK_8001bb6194cd9ad717606002b20" FOREIGN KEY ("userId") REFERENCES public.users(id);


--
-- Name: apps FK_860fb2ed99a000c335715c0d7b0; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.apps
    ADD CONSTRAINT "FK_860fb2ed99a000c335715c0d7b0" FOREIGN KEY ("goalCategoryId") REFERENCES public.goal_categories(id);


--
-- Name: user_apps FK_884ba4e0d8cd4b80fe912c93db0; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_apps
    ADD CONSTRAINT "FK_884ba4e0d8cd4b80fe912c93db0" FOREIGN KEY ("userId") REFERENCES public.users(id);


--
-- Name: country_languages FK_89dc703d8ca945151a4fb0945cd; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.country_languages
    ADD CONSTRAINT "FK_89dc703d8ca945151a4fb0945cd" FOREIGN KEY ("countriesId") REFERENCES public.countries(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: user_messages FK_8f211af20e47fff29862054ac56; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_messages
    ADD CONSTRAINT "FK_8f211af20e47fff29862054ac56" FOREIGN KEY ("messageId") REFERENCES public.messages(id);


--
-- Name: users FK_9f9c3548c0fa4efecb1e0f292dc; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT "FK_9f9c3548c0fa4efecb1e0f292dc" FOREIGN KEY ("secondaryLanguageId") REFERENCES public.languages(id);


--
-- Name: goals FK_a486d9bb93d1d26ac5b8dd78600; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.goals
    ADD CONSTRAINT "FK_a486d9bb93d1d26ac5b8dd78600" FOREIGN KEY ("goalCategoryId") REFERENCES public.goal_categories(id);


--
-- Name: country_languages FK_b321147e5c326be40fc9c68c517; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.country_languages
    ADD CONSTRAINT "FK_b321147e5c326be40fc9c68c517" FOREIGN KEY ("languagesId") REFERENCES public.languages(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: user_goal_priorities FK_bba7a20d94bd8e16204a2bb6b99; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_goal_priorities
    ADD CONSTRAINT "FK_bba7a20d94bd8e16204a2bb6b99" FOREIGN KEY ("goalPriorityId") REFERENCES public.goal_priorities(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: user_goal_categories FK_bd6ac8878c150cb1b9469fc96d4; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_goal_categories
    ADD CONSTRAINT "FK_bd6ac8878c150cb1b9469fc96d4" FOREIGN KEY ("goalCategoryId") REFERENCES public.goal_categories(id);


--
-- Name: goal_priorities FK_be5edb7aad1a24725d54573a56f; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.goal_priorities
    ADD CONSTRAINT "FK_be5edb7aad1a24725d54573a56f" FOREIGN KEY ("goalCategoryId") REFERENCES public.goal_categories(id);


--
-- Name: user_goals FK_c14a9a2e19a021a11de6775564e; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_goals
    ADD CONSTRAINT "FK_c14a9a2e19a021a11de6775564e" FOREIGN KEY ("userId") REFERENCES public.users(id);


--
-- Name: user_apps FK_cacf8c78ceb44d2dcb0f8f67247; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_apps
    ADD CONSTRAINT "FK_cacf8c78ceb44d2dcb0f8f67247" FOREIGN KEY ("appId") REFERENCES public.apps(id);


--
-- Name: users FK_cc0dc7234854a65964f1a268275; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT "FK_cc0dc7234854a65964f1a268275" FOREIGN KEY ("countryId") REFERENCES public.countries(id);


--
-- Name: apps FK_d521f3c1b656d9ba063247f670c; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.apps
    ADD CONSTRAINT "FK_d521f3c1b656d9ba063247f670c" FOREIGN KEY ("countryCode") REFERENCES public.countries(code);


--
-- Name: users FK_e82afcf2bc3e13cfdd1a313112f; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT "FK_e82afcf2bc3e13cfdd1a313112f" FOREIGN KEY ("primaryLanguageId") REFERENCES public.languages(id);


--
-- Name: app_goals FK_f5217329c699f0327b2d9cb9c2a; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.app_goals
    ADD CONSTRAINT "FK_f5217329c699f0327b2d9cb9c2a" FOREIGN KEY ("goalsId") REFERENCES public.goals(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: messages FK_fa26bb110a3cb2ea576a10bb766; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT "FK_fa26bb110a3cb2ea576a10bb766" FOREIGN KEY ("coachId") REFERENCES public.admin_users(id);


--
-- Name: interventions_log interventions_log_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.interventions_log
    ADD CONSTRAINT interventions_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: rewards_issued rewards_issued_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rewards_issued
    ADD CONSTRAINT rewards_issued_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--

\unrestrict IiXr59D4RPphNSd6DitSZtJFZFyfsqhNk3FHs53EWv56A2ywfvf1WGQHxx1Gmp8

