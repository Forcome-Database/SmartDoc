CREATE TYPE "public"."document_status" AS ENUM('draft', 'published', 'archived');--> statement-breakpoint
CREATE TYPE "public"."nav_menu_target_type" AS ENUM('category', 'document', 'external', 'none');--> statement-breakpoint
CREATE TYPE "public"."nav_menu_type" AS ENUM('link', 'dropdown', 'divider');--> statement-breakpoint
CREATE TYPE "public"."translation_status" AS ENUM('pending', 'processing', 'completed', 'failed');--> statement-breakpoint
CREATE TYPE "public"."user_role" AS ENUM('admin', 'editor', 'viewer');--> statement-breakpoint
CREATE TABLE "categories" (
	"id" text PRIMARY KEY NOT NULL,
	"parent_id" text,
	"slug" text NOT NULL,
	"sort_order" integer DEFAULT 0 NOT NULL,
	"created_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "category_titles" (
	"id" text PRIMARY KEY NOT NULL,
	"category_id" text NOT NULL,
	"locale_id" text NOT NULL,
	"title" text NOT NULL,
	CONSTRAINT "category_titles_category_id_locale_id_unique" UNIQUE("category_id","locale_id")
);
--> statement-breakpoint
CREATE TABLE "documents" (
	"id" text PRIMARY KEY NOT NULL,
	"category_id" text,
	"author_id" text NOT NULL,
	"locale_id" text NOT NULL,
	"title" text NOT NULL,
	"slug" text NOT NULL,
	"content" text DEFAULT '' NOT NULL,
	"status" "document_status" DEFAULT 'draft' NOT NULL,
	"published_version" integer,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL,
	CONSTRAINT "documents_category_id_locale_id_slug_unique" UNIQUE("category_id","locale_id","slug")
);
--> statement-breakpoint
CREATE TABLE "edit_locks" (
	"id" text PRIMARY KEY NOT NULL,
	"document_id" text NOT NULL,
	"user_id" text NOT NULL,
	"acquired_at" timestamp DEFAULT now() NOT NULL,
	"expires_at" timestamp NOT NULL,
	CONSTRAINT "edit_locks_document_id_unique" UNIQUE("document_id")
);
--> statement-breakpoint
CREATE TABLE "locales" (
	"id" text PRIMARY KEY NOT NULL,
	"code" text NOT NULL,
	"name" text NOT NULL,
	"native_name" text NOT NULL,
	"is_default" boolean DEFAULT false NOT NULL,
	"is_enabled" boolean DEFAULT true NOT NULL,
	"sort_order" integer DEFAULT 0 NOT NULL,
	"created_at" timestamp DEFAULT now() NOT NULL,
	CONSTRAINT "locales_code_unique" UNIQUE("code")
);
--> statement-breakpoint
CREATE TABLE "nav_menu_titles" (
	"id" text PRIMARY KEY NOT NULL,
	"nav_menu_id" text NOT NULL,
	"locale_id" text NOT NULL,
	"title" text NOT NULL,
	CONSTRAINT "nav_menu_titles_nav_menu_id_locale_id_unique" UNIQUE("nav_menu_id","locale_id")
);
--> statement-breakpoint
CREATE TABLE "nav_menus" (
	"id" text PRIMARY KEY NOT NULL,
	"parent_id" text,
	"type" "nav_menu_type" DEFAULT 'link' NOT NULL,
	"target_type" "nav_menu_target_type" DEFAULT 'none' NOT NULL,
	"target_id" text,
	"external_url" text,
	"open_in_new_tab" boolean DEFAULT false NOT NULL,
	"icon" text,
	"sort_order" integer DEFAULT 0 NOT NULL,
	"is_visible" boolean DEFAULT true NOT NULL,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "translations" (
	"id" text PRIMARY KEY NOT NULL,
	"document_id" text NOT NULL,
	"source_locale_id" text NOT NULL,
	"target_locale_id" text NOT NULL,
	"status" "translation_status" DEFAULT 'pending' NOT NULL,
	"result" text,
	"created_by" text NOT NULL,
	"created_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "users" (
	"id" text PRIMARY KEY NOT NULL,
	"dingtalk_id" text NOT NULL,
	"union_id" text,
	"name" text NOT NULL,
	"avatar" text,
	"email" text,
	"mobile" text,
	"department" text,
	"department_id" text,
	"role" "user_role" DEFAULT 'editor' NOT NULL,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL,
	CONSTRAINT "users_dingtalk_id_unique" UNIQUE("dingtalk_id"),
	CONSTRAINT "users_union_id_unique" UNIQUE("union_id")
);
--> statement-breakpoint
CREATE TABLE "versions" (
	"id" text PRIMARY KEY NOT NULL,
	"document_id" text NOT NULL,
	"version_num" integer NOT NULL,
	"content" text NOT NULL,
	"change_log" text,
	"author_id" text NOT NULL,
	"created_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
ALTER TABLE "categories" ADD CONSTRAINT "categories_parent_id_categories_id_fk" FOREIGN KEY ("parent_id") REFERENCES "public"."categories"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "category_titles" ADD CONSTRAINT "category_titles_category_id_categories_id_fk" FOREIGN KEY ("category_id") REFERENCES "public"."categories"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "category_titles" ADD CONSTRAINT "category_titles_locale_id_locales_id_fk" FOREIGN KEY ("locale_id") REFERENCES "public"."locales"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "documents" ADD CONSTRAINT "documents_category_id_categories_id_fk" FOREIGN KEY ("category_id") REFERENCES "public"."categories"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "documents" ADD CONSTRAINT "documents_author_id_users_id_fk" FOREIGN KEY ("author_id") REFERENCES "public"."users"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "documents" ADD CONSTRAINT "documents_locale_id_locales_id_fk" FOREIGN KEY ("locale_id") REFERENCES "public"."locales"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "edit_locks" ADD CONSTRAINT "edit_locks_document_id_documents_id_fk" FOREIGN KEY ("document_id") REFERENCES "public"."documents"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "edit_locks" ADD CONSTRAINT "edit_locks_user_id_users_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "nav_menu_titles" ADD CONSTRAINT "nav_menu_titles_nav_menu_id_nav_menus_id_fk" FOREIGN KEY ("nav_menu_id") REFERENCES "public"."nav_menus"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "nav_menu_titles" ADD CONSTRAINT "nav_menu_titles_locale_id_locales_id_fk" FOREIGN KEY ("locale_id") REFERENCES "public"."locales"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "nav_menus" ADD CONSTRAINT "nav_menus_parent_id_nav_menus_id_fk" FOREIGN KEY ("parent_id") REFERENCES "public"."nav_menus"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "translations" ADD CONSTRAINT "translations_document_id_documents_id_fk" FOREIGN KEY ("document_id") REFERENCES "public"."documents"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "translations" ADD CONSTRAINT "translations_source_locale_id_locales_id_fk" FOREIGN KEY ("source_locale_id") REFERENCES "public"."locales"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "translations" ADD CONSTRAINT "translations_target_locale_id_locales_id_fk" FOREIGN KEY ("target_locale_id") REFERENCES "public"."locales"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "translations" ADD CONSTRAINT "translations_created_by_users_id_fk" FOREIGN KEY ("created_by") REFERENCES "public"."users"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "versions" ADD CONSTRAINT "versions_document_id_documents_id_fk" FOREIGN KEY ("document_id") REFERENCES "public"."documents"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "versions" ADD CONSTRAINT "versions_author_id_users_id_fk" FOREIGN KEY ("author_id") REFERENCES "public"."users"("id") ON DELETE no action ON UPDATE no action;