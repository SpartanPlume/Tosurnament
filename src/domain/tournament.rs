use crate::domain::tournament_acronym::TournamentAcronym;
use crate::domain::tournament_name::TournamentName;

pub struct Tournament {
    pub name: TournamentName,
    pub acronym: TournamentAcronym,
}
