import azure.functions as func
import logging
import mysql.connector
import pandas as pd
import json
from datetime import datetime

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="http_trigger17")
def http_trigger17(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Function processed a request")
    try:
        # Load the JSON data from the request
        req_body = req.get_json()

        # Transform JSON to DataFrame
        all_metrics = []
        for metric in req_body['data']['metrics']:
            df = pd.DataFrame(metric['data'])
            df['metric'] = metric['name']  # Add a column for the metric name
            df['units'] = metric['units']  # Add a column for the units
            all_metrics.append(df)
            
        final_df = pd.concat(all_metrics, ignore_index=True)
    except Exception as e:
        logging.info(f"Error: {str(e)}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
    
    try:

        # Adjust DataFrame structure
        final_df['date'] = pd.to_datetime(final_df['date'])
        final_df['date'] = final_df['date'].dt.strftime('%Y-%m-%d %H:%M:%S')

        heart_rate_data = final_df[final_df['metric'] == 'heart_rate'].copy()
        heart_rate_data['heart_rate_Min_bpm'] = heart_rate_data['Min']
        heart_rate_data['heart_rate_Avg_bpm'] = heart_rate_data['Avg']
        heart_rate_data['heart_rate_Max_bpm'] = heart_rate_data['Max']
        final_df = final_df[final_df['metric'] != 'heart_rate']
        final_df = final_df.append(heart_rate_data, ignore_index=True)
        final_df.drop(columns=['Min', 'Avg', 'Max'], errors='ignore', inplace=True)
        final_df['metric_unit'] = final_df.apply(lambda x: f"{x['metric']}_{x['units']}" if pd.notnull(x['qty']) else f"{x['metric']}_bpm", axis=1)

        # Pivot DataFrame
        pivoted_df = final_df.pivot_table(index='date', 
                                           columns='metric_unit', 
                                           values=['qty', 'heart_rate_Min_bpm', 'heart_rate_Avg_bpm', 'heart_rate_Max_bpm'],
                                           aggfunc='first').reset_index()
        pivoted_df.columns = ['_'.join(col).strip() if col[1] else col[0] for col in pivoted_df.columns.values]
        pivoted_df.reset_index(inplace=True, drop=True)
        pivoted_df=pivoted_df.fillna(0)
    
    except Exception as e:
        logging.info(f"Error: {str(e)}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
    
    try:
        # Database connection parameters
        config = {
            'user': os.getenv("USER_NAME"),
            'password': os.getenv("PASSWORD"),
            'host': os.getenv("HOST_NAME"),
            'database': os.getenv("DATABASE")
        }

        # Establish a connection to the database
        cnx = mysql.connector.connect(**config)
        cursor = cnx.cursor()

        # Insert rows into the Reading and HeartRate tables
        for index, row in pivoted_df.iterrows():
            try:
                # Prepare the insert statement for the Reading table
                reading_insert_query = """
                    INSERT INTO Reading (DeviceID, Date, ActiveEnergy_kJ, RestingEnergy_kJ, RestingHeartRate_bpm,
                      FlightsClimbed,
                      HeadphoneAudioExposure_dBASPL,
                      StepCount_steps,
                      WalkingRunningDistance_km,
                      WalkingSpeed_kmhr,
                      WalkingStepLength_cm,
                      WalkingAsymmetry_Percentage,
                      WalkingDoubleSupport_Percentage) 
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

                reading_data = (
                    1,  
                    row['date'],
                    row['qty_active_energy_kJ'],
                    row["qty_basal_energy_burned_kJ"],
                    row["qty_resting_heart_rate_count/min"],
                    row["qty_flights_climbed_count"],
                    row["qty_headphone_audio_exposure_dBASPL"],
                    row["qty_step_count_count"],
                    row["qty_walking_running_distance_km"],
                    row["qty_walking_speed_km/hr"],
                    row["qty_walking_step_length_cm"],
                    row["qty_walking_asymmetry_percentage_%"],
                    row["qty_walking_double_support_percentage_%"]
                )
                cursor.execute(reading_insert_query, reading_data)
                reading_id = cursor.lastrowid  # Get the generated id

                # Prepare the insert statement for the HeartRate table
                heart_rate_insert_query = """
                    INSERT INTO HeartRate (ReadingID, HeartRateMin_bpm, HeartRateMax_bpm, HeartRateAvg_bpm) 
                    VALUES (%s, %s, %s, %s)
                """
                heart_rate_data = (
                    reading_id,
                    row['heart_rate_Min_bpm_heart_rate_bpm'],
                    row['heart_rate_Max_bpm_heart_rate_bpm'],
                    row['heart_rate_Avg_bpm_heart_rate_bpm'],
                )
                cursor.execute(heart_rate_insert_query, heart_rate_data)

                # Commit the transaction
                cnx.commit()
            except mysql.connector.Error as err:
                print("Error:", err)
                cnx.rollback()  # Rollback the transaction in case of an error
                logging.info(f"Error: {str(e)}")
                return func.HttpResponse(f"Error: {str(err)}", status_code=500)

        # Close the cursor and connection
        cursor.close()
        cnx.close()

    except Exception as e:
        logging.info(f"Error: {str(e)}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
    logging.info("Data processed successfully")
    return func.HttpResponse("Data processed successfully.", status_code=200)

