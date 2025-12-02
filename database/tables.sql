CREATE TABLE public.auth_group (
    id integer NOT NULL,
    name character varying(150) NOT NULL
);
CREATE TABLE public.auth_group_permissions (
    id bigint NOT NULL,
    group_id integer NOT NULL,
    permission_id integer NOT NULL
);
CREATE TABLE public.auth_permission (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    content_type_id integer NOT NULL,
    codename character varying(100) NOT NULL
);
CREATE TABLE public.auth_user (
    id integer NOT NULL,
    password character varying(128) NOT NULL,
    last_login timestamp with time zone,
    is_superuser boolean NOT NULL,
    username character varying(150) NOT NULL,
    first_name character varying(150) NOT NULL,
    last_name character varying(150) NOT NULL,
    email character varying(254) NOT NULL,
    is_staff boolean NOT NULL,
    is_active boolean NOT NULL,
    date_joined timestamp with time zone NOT NULL
);
CREATE TABLE public.auth_user_groups (
    id bigint NOT NULL,
    user_id integer NOT NULL,
    group_id integer NOT NULL
);
CREATE TABLE public.auth_user_user_permissions (
    id bigint NOT NULL,
    user_id integer NOT NULL,
    permission_id integer NOT NULL
);
CREATE TABLE public.base_contractevent (
    event_id uuid NOT NULL,
    event_type character varying(100) NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    tx_hash character varying(255) NOT NULL,
    proposal_id uuid,
    round_id uuid
);
CREATE TABLE public.base_donation (
    donation_id uuid NOT NULL,
    amount numeric(20,8) NOT NULL,
    sybil_score double precision NOT NULL,
    tx_hash character varying(255) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    donor_id uuid NOT NULL,
    proposal_id uuid NOT NULL
);
CREATE TABLE public.base_donor (
    donor_id uuid NOT NULL,
    username character varying(100) NOT NULL,
    reputation_score double precision NOT NULL,
    joined_at timestamp with time zone NOT NULL,
    wallet_id uuid NOT NULL
);
CREATE TABLE public.base_governancetoken (
    holder_id uuid NOT NULL,
    voting_power numeric(20,8) NOT NULL,
    role character varying(10) NOT NULL,
    wallet_id uuid NOT NULL
);
CREATE TABLE public.base_match (
    match_id uuid NOT NULL,
    matched_amount numeric(20,8) NOT NULL,
    proposal_id uuid NOT NULL,
    round_id uuid NOT NULL
);
CREATE TABLE public.base_matchingpool (
    pool_id uuid NOT NULL,
    total_funds numeric(20,8) NOT NULL,
    allocated_funds numeric(20,8) NOT NULL,
    replenished_by character varying(100) NOT NULL
);
CREATE TABLE public.base_payout (
    payout_id uuid NOT NULL,
    amount numeric(20,8) NOT NULL,
    tx_hash character varying(255) NOT NULL,
    distributed_at timestamp with time zone NOT NULL,
    proposal_id uuid NOT NULL,
    round_id uuid NOT NULL
);
CREATE TABLE public.base_proposal (
    proposal_id uuid NOT NULL,
    title character varying(255) NOT NULL,
    description text NOT NULL,
    status character varying(10) NOT NULL,
    total_donations numeric(20,8) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    proposer_id uuid NOT NULL,
    round_id uuid NOT NULL
);
CREATE TABLE public.base_qfresult (
    result_id uuid NOT NULL,
    calculated_match numeric(20,8) NOT NULL,
    verified boolean NOT NULL,
    proposal_id uuid NOT NULL,
    round_id uuid NOT NULL
);
CREATE TABLE public.base_round (
    round_id uuid NOT NULL,
    start_date timestamp with time zone NOT NULL,
    end_date timestamp with time zone NOT NULL,
    status character varying(10) NOT NULL,
    matching_pool_id uuid NOT NULL
);
CREATE TABLE public.base_sybilscore (
    score_id uuid NOT NULL,
    score double precision NOT NULL,
    verified_by character varying(100) NOT NULL,
    last_updated timestamp with time zone NOT NULL,
    wallet_id uuid NOT NULL
);
CREATE TABLE public.base_wallet (
    wallet_id uuid NOT NULL,
    address character varying(255) NOT NULL,
    balance numeric(20,8) NOT NULL,
    status character varying(10) NOT NULL,
    last_activity timestamp with time zone NOT NULL
);
CREATE TABLE public.django_admin_log (
    id integer NOT NULL,
    action_time timestamp with time zone NOT NULL,
    object_id text,
    object_repr character varying(200) NOT NULL,
    action_flag smallint NOT NULL,
    change_message text NOT NULL,
    content_type_id integer,
    user_id integer NOT NULL,
    CONSTRAINT django_admin_log_action_flag_check CHECK ((action_flag >= 0))
);
CREATE TABLE public.django_content_type (
    id integer NOT NULL,
    app_label character varying(100) NOT NULL,
    model character varying(100) NOT NULL
);
CREATE TABLE public.django_migrations (
    id bigint NOT NULL,
    app character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    applied timestamp with time zone NOT NULL
);
CREATE TABLE public.django_session (
    session_key character varying(40) NOT NULL,
    session_data text NOT NULL,
    expire_date timestamp with time zone NOT NULL
);
