create table if not exists problems (
    id serial primary key,
    description text not null
);

create table if not exists users (
    id serial primary key,
    rank varchar(255) not null default 'unranked'
);

create table if not exists submissions (
    id serial primary key,
    problem_id integer not null references problems(id) on delete cascade,
    user_id integer not null references users(id) on delete cascade,
    code text not null CHECK (octet_length(code) <= 1024 * 1024),
    status varchar(255) not null default 'pending',
    memory_usage BIGINT,
    time_usage NUMERIC(10, 3),
    verdict varchar(255)
);
