CREATE SCHEMA "public";
CREATE TYPE "case_status" AS ENUM('RECEIVED', 'DISPATCHED', 'AIRBORNE', 'LANDED', 'COMPLETED', 'CANCELLED');
CREATE TYPE "contact_role" AS ENUM('NURSE', 'NEXT_OF_KIN', 'AGENT', 'HOSPITAL');
CREATE TYPE "notif_role" AS ENUM('NURSE', 'AGENT', 'HOSPITAL', 'NEXT_OF_KIN');
CREATE TYPE "notif_channel" AS ENUM('SMS', 'USSD');
CREATE TYPE "notif_status" AS ENUM('PENDING', 'SENT', 'FAILED');
CREATE TYPE "ussd_outcome" AS ENUM('CASE_CREATED', 'STATUS_CHECKED', 'ABANDONED', 'CANCELLED');
CREATE TYPE "operator_role" AS ENUM('ADMIN', 'DISPATCHER', 'VIEWER');
CREATE TABLE "airstrips" (
	"icao_code" varchar(10) PRIMARY KEY,
	"iata_code" varchar(10),
	"name" varchar(200) NOT NULL,
	"airport_type" varchar(30),
	"city" varchar(80),
	"county" varchar(80),
	"county_code" varchar(80),
	"latitude" double precision,
	"longitude" double precision,
	"elevation_ft" integer,
	"scheduled_service" boolean,
	"agent_phone" varchar(20),
	"updated_at" timestamp with time zone DEFAULT now()
);
CREATE TABLE "case_contacts" (
	"id" serial PRIMARY KEY,
	"case_id" varchar(20) NOT NULL,
	"role" contact_role NOT NULL,
	"phone_raw" varchar(20) NOT NULL,
	"phone_masked" varchar(20) NOT NULL,
	"name" varchar(100),
	"notified_at" timestamp with time zone
);
CREATE TABLE "case_status_history" (
	"id" serial PRIMARY KEY,
	"case_id" varchar(20) NOT NULL,
	"from_status" varchar(20),
	"to_status" varchar(20) NOT NULL,
	"changed_by" varchar(60) NOT NULL,
	"notes" text,
	"eta_minutes" integer,
	"changed_at" timestamp with time zone DEFAULT now() NOT NULL
);
CREATE TABLE "cases" (
	"id" varchar(20) PRIMARY KEY,
	"condition_code" varchar(2) NOT NULL,
	"condition_name" varchar(100) NOT NULL,
	"airstrip_code" varchar(10) NOT NULL,
	"airstrip_name" varchar(100) NOT NULL,
	"initiating_phone" varchar(20) NOT NULL,
	"status" case_status NOT NULL,
	"eta_minutes" integer,
	"notes" text,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now()
);
CREATE TABLE "conditions" (
	"code" varchar(2) PRIMARY KEY,
	"name" varchar(100) NOT NULL,
	"description" text,
	"priority" integer NOT NULL,
	"is_active" boolean NOT NULL
);
CREATE TABLE "hospitals" (
	"id" serial PRIMARY KEY,
	"name" varchar(120) NOT NULL,
	"phone" varchar(20) NOT NULL,
	"county" varchar(80),
	"latitude" double precision,
	"longitude" double precision,
	"is_default" boolean NOT NULL,
	"is_active" boolean NOT NULL
);
CREATE TABLE "notifications" (
	"id" serial PRIMARY KEY,
	"case_id" varchar(20),
	"recipient_phone" varchar(20) NOT NULL,
	"recipient_role" notif_role NOT NULL,
	"channel" notif_channel NOT NULL,
	"message_preview" varchar(100),
	"at_message_id" varchar(60),
	"status" notif_status NOT NULL,
	"cost" varchar(20),
	"error_detail" text,
	"sent_at" timestamp with time zone DEFAULT now() NOT NULL
);
CREATE TABLE "operators" (
	"id" serial PRIMARY KEY,
	"username" varchar(60) NOT NULL,
	"password_hash" varchar(128) NOT NULL,
	"full_name" varchar(100),
	"role" operator_role NOT NULL,
	"is_active" boolean NOT NULL,
	"last_login_at" timestamp with time zone,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
CREATE TABLE "ussd_sessions" (
	"session_id" varchar(60) PRIMARY KEY,
	"phone" varchar(20) NOT NULL,
	"service_code" varchar(20),
	"final_text" varchar(200),
	"case_created" varchar(20),
	"outcome" ussd_outcome,
	"started_at" timestamp with time zone DEFAULT now() NOT NULL,
	"ended_at" timestamp with time zone
);
CREATE UNIQUE INDEX "airstrips_pkey" ON "airstrips" ("icao_code");
CREATE UNIQUE INDEX "case_contacts_pkey" ON "case_contacts" ("id");
CREATE INDEX "ix_case_contacts_case_id" ON "case_contacts" ("case_id");
CREATE UNIQUE INDEX "case_status_history_pkey" ON "case_status_history" ("id");
CREATE INDEX "ix_case_status_history_case_id" ON "case_status_history" ("case_id");
CREATE UNIQUE INDEX "cases_pkey" ON "cases" ("id");
CREATE INDEX "ix_cases_airstrip_code" ON "cases" ("airstrip_code");
CREATE INDEX "ix_cases_condition_code" ON "cases" ("condition_code");
CREATE INDEX "ix_cases_status" ON "cases" ("status");
CREATE UNIQUE INDEX "conditions_pkey" ON "conditions" ("code");
CREATE UNIQUE INDEX "hospitals_pkey" ON "hospitals" ("id");
CREATE INDEX "ix_notifications_case_id" ON "notifications" ("case_id");
CREATE UNIQUE INDEX "notifications_pkey" ON "notifications" ("id");
CREATE UNIQUE INDEX "ix_operators_username" ON "operators" ("username");
CREATE UNIQUE INDEX "operators_pkey" ON "operators" ("id");
CREATE INDEX "ix_ussd_sessions_phone" ON "ussd_sessions" ("phone");
CREATE UNIQUE INDEX "ussd_sessions_pkey" ON "ussd_sessions" ("session_id");
