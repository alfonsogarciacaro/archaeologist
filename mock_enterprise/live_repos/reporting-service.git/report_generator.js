// Reporting Service JavaScript Module
// Handles generating financial reports and analytics

const axios = require('axios');

class ReportGenerator {
    constructor() {
        this.userServiceUrl = process.env.USER_SERVICE_URL || 'http://localhost:8001';
        this.dbConnection = null;
    }

    // Generate term sheet report using term_sheet_id
    async generateTermSheetReport(termSheetId) {
        try {
            // Query database using the legacy term_sheet_id string
            const query = `
                SELECT ts.*, u.email, u.client_identifier 
                FROM term_sheets ts 
                JOIN users u ON ts.user_id = u.id 
                WHERE ts.term_sheet_id = ?
            `;
            
            const result = await this.dbConnection.execute(query, [termSheetId]);
            
            if (result.rows.length === 0) {
                throw new Error(`Term sheet with ID ${termSheetId} not found`);
            }

            const termSheet = result.rows[0];
            
            // Generate report data
            const reportData = {
                termSheetId: termSheet.term_sheet_id,
                clientId: termSheet.client_identifier,
                userEmail: termSheet.email,
                amount: termSheet.amount,
                status: termSheet.status,
                generatedAt: new Date().toISOString()
            };

            return await this.formatReport(reportData);
        } catch (error) {
            console.error('Error generating term sheet report:', error);
            throw error;
        }
    }

    // Search term sheets by client identifier
    async searchByClientIdentifier(clientIdentifier) {
        const query = `
            SELECT ts.*, u.email 
            FROM term_sheets ts 
            JOIN users u ON ts.user_id = u.id 
            WHERE u.client_identifier ILIKE ?
            ORDER BY ts.created_at DESC
        `;
        
        const result = await this.dbConnection.execute(query, [`%${clientIdentifier}%`]);
        return result.rows;
    }

    // Format report for display
    async formatReport(data) {
        return {
            reportType: 'term_sheet_summary',
            data: data,
            metadata: {
                generatedBy: 'reporting-service',
                timestamp: new Date().toISOString(),
                version: '1.0.0'
            }
        };
    }

    // Export term sheet to Excel (for integration with VBA macros)
    async exportToExcel(termSheetId) {
        const report = await this.generateTermSheetReport(termSheetId);
        
        // This would integrate with the existing Excel VBA macros
        // by generating CSV/Excel files that the macros can process
        const exportData = {
            term_sheet_id: report.data.termSheetId,
            client_id: report.data.clientId,
            amount: report.data.amount,
            export_timestamp: new Date().toISOString()
        };

        return exportData;
    }
}

module.exports = { ReportGenerator };