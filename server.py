# server.py

from flask import Flask, jsonify
import pandas as pd
from utils import engine

def register_api_routes(server: Flask):
    @server.route('/api/v1/transactions', methods=['GET'])
    def get_transactions():
        try:
            master_q = (
                "SELECT TOP 1 table_name FROM dbo.MasterTable "
                "WHERE table_name LIKE 'transactions_%' "
                "ORDER BY uploaded_at DESC"
            )
            mdf = pd.read_sql(master_q, engine)
            if mdf.empty:
                return jsonify([])
            tbl = mdf.loc[0, 'table_name']
            df = pd.read_sql(f"SELECT TOP 100 * FROM dbo.{tbl}", engine)
            return jsonify(df.to_dict(orient='records'))
        except Exception as e:
            return jsonify({'error': str(e)}), 500
