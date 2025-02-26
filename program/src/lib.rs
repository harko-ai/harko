use anchor_lang::prelude::*;

declare_id!("your_program_id");

#[program]
pub mod Harko {
    use super::*;

    pub fn initialize_agent(ctx: Context<InitializeAgent>, agent_name: String) -> Result<()> {
        let agent = &mut ctx.accounts.agent;
        agent.owner = ctx.accounts.owner.key();
        agent.name = agent_name;
        agent.is_active = true;
        agent.voice_sessions = 0;
        Ok(())
    }

    pub fn start_voice_session(ctx: Context<StartVoiceSession>, session_id: String) -> Result<()> {
        let session = &mut ctx.accounts.voice_session;
        let agent = &mut ctx.accounts.agent;

        session.agent = agent.key();
        session.session_id = session_id;
        session.start_time = Clock::get()?.unix_timestamp;
        session.is_active = true;
        session.data_chunks = 0;

        agent.voice_sessions += 1;
        Ok(())
    }

    pub fn store_voice_data(
        ctx: Context<StoreVoiceData>,
        data_hash: String,
        chunk_number: u64,
        duration: i64,
    ) -> Result<()> {
        let voice_data = &mut ctx.accounts.voice_data;
        let session = &mut ctx.accounts.voice_session;

        require!(session.is_active, HarkoError::SessionInactive);

        voice_data.session = session.key();
        voice_data.data_hash = data_hash;
        voice_data.chunk_number = chunk_number;
        voice_data.timestamp = Clock::get()?.unix_timestamp;
        voice_data.duration = duration;

        session.data_chunks += 1;
        Ok(())
    }

    pub fn end_voice_session(ctx: Context<EndVoiceSession>) -> Result<()> {
        let session = &mut ctx.accounts.voice_session;
        require!(session.is_active, HarkoError::SessionInactive);

        session.is_active = false;
        session.end_time = Clock::get()?.unix_timestamp;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct InitializeAgent<'info> {
    #[account(
        init,
        payer = owner,
        space = 8 + 32 + 200 + 1 + 8
    )]
    pub agent: Account<'info, Agent>,
    #[account(mut)]
    pub owner: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct StartVoiceSession<'info> {
    #[account(
        init,
        payer = owner,
        space = 8 + 32 + 100 + 8 + 1 + 8 + 8
    )]
    pub voice_session: Account<'info, VoiceSession>,
    #[account(mut)]
    pub agent: Account<'info, Agent>,
    #[account(mut)]
    pub owner: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct StoreVoiceData<'info> {
    #[account(
        init,
        payer = owner,
        space = 8 + 32 + 100 + 8 + 8 + 8
    )]
    pub voice_data: Account<'info, VoiceData>,
    #[account(mut)]
    pub voice_session: Account<'info, VoiceSession>,
    #[account(mut)]
    pub owner: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct EndVoiceSession<'info> {
    #[account(mut)]
    pub voice_session: Account<'info, VoiceSession>,
    pub owner: Signer<'info>,
}

#[account]
pub struct Agent {
    pub owner: Pubkey,
    pub name: String,
    pub is_active: bool,
    pub voice_sessions: u64,
}

#[account]
pub struct VoiceSession {
    pub agent: Pubkey,
    pub session_id: String,
    pub start_time: i64,
    pub end_time: i64,
    pub is_active: bool,
    pub data_chunks: u64,
}

#[account]
pub struct VoiceData {
    pub session: Pubkey,
    pub data_hash: String,
    pub chunk_number: u64,
    pub timestamp: i64,
    pub duration: i64,
}

#[error_code]
pub enum HarkoError {
    #[msg("Voice session is not active")]
    SessionInactive,
}
