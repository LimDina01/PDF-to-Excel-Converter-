import os
import io
import time
import pandas as pd
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import FileResponse, JsonResponse
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from convert_statement import extract_bank_statement
from banks.ocr_utils import is_ocr_available
from .models import ConversionLog

def check_reconciliation(df):
    """
    Checks if running balance equals prev_balance + money_in - money_out.
    Returns (status_text, is_balanced)
    """
    bal_col = next((c for c in df.columns if 'BALANCE' in c.upper()), None)
    in_col = next((c for c in df.columns if any(k in c.upper() for k in ['MONEY IN', 'CR', 'CREDIT', 'CASH IN'])), None)
    out_col = next((c for c in df.columns if any(k in c.upper() for k in ['MONEY OUT', 'DR', 'DEBIT', 'CASH OUT'])), None)

    if not bal_col:
        return f"{len(df)} transactions", True

    def to_float(v):
        if pd.isna(v) or v == '': return 0.0
        s = str(v).replace(',', '').strip()
        try: return float(s)
        except: return 0.0

    bals = [to_float(v) for v in df[bal_col]]
    ins = [to_float(v) for v in df[in_col]] if in_col else [0.0] * len(bals)
    outs = [to_float(v) for v in df[out_col]] if out_col else [0.0] * len(bals)

    discrepancies = 0
    for idx in range(1, len(bals)):
        expected = round(bals[idx - 1] + ins[idx] - outs[idx], 2)
        actual = round(bals[idx], 2)
        if abs(expected - actual) > 0.05:
            discrepancies += 1

    if discrepancies == 0:
        return f"Balanced ({len(df)} txns)", True
    else:
        return f"Discrepancies ({discrepancies} rows)", False

@login_required
def index(request):
    ocr_supported = is_ocr_available()
    if request.method == 'POST' and request.FILES.get('pdf_file'):
        pdf_file = request.FILES['pdf_file']
        bank = request.POST.get('bank', 'Auto-Detect')
        include_summary = request.POST.get('include_summary') in ['on', 'true', '1']
        use_ocr = request.POST.get('use_ocr') in ['on', 'true', '1'] if 'use_ocr' in request.POST else ocr_supported
        export_format = request.POST.get('export_format', 'csv')
        original_filename = pdf_file.name
        file_size_kb = round(pdf_file.size / 1024, 1) if hasattr(pdf_file, 'size') else 0.0
        start_time = time.time()
        
        # Initialize the log entry
        log = ConversionLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            filename=original_filename,
            file_size_kb=file_size_kb,
            bank_selected=bank,
            include_summary=include_summary,
            export_format=export_format,
            is_successful=False
        )
        
        fs = FileSystemStorage()
        filename = fs.save(pdf_file.name, pdf_file)
        pdf_path = fs.path(filename)
        
        # Output path
        output_filename = os.path.splitext(filename)[0] + "_converted.csv"
        output_path = os.path.join(settings.MEDIA_ROOT, output_filename)
        
        try:
            success = extract_bank_statement(pdf_path, output_path, bank=bank, include_summary=include_summary, use_ocr=use_ocr)
            
            # Delete the original PDF file immediately for privacy
            try:
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
            except Exception:
                pass
                
            if success:
                log.is_successful = True
                
                # Check row count and ledger integrity from CSV before cleanup
                try:
                    if os.path.exists(output_path):
                        df_check = pd.read_csv(output_path)
                        log.transactions_count = len(df_check)
                        recon_text, _ = check_reconciliation(df_check)
                        log.reconciliation_status = recon_text
                except Exception:
                    log.reconciliation_status = "N/A"
                    
                log.duration_seconds = round(time.time() - start_time, 2)
                log.save()
                
                def attach_audit_headers(resp):
                    resp['X-Transactions-Count'] = str(log.transactions_count)
                    resp['X-Reconciliation-Status'] = str(log.reconciliation_status or '')
                    resp['Access-Control-Expose-Headers'] = 'Content-Disposition, X-Transactions-Count, X-Reconciliation-Status'
                    return resp
                
                if export_format == 'excel':
                    excel_filename = os.path.splitext(filename)[0] + "_converted.xlsx"
                    excel_path = os.path.join(settings.MEDIA_ROOT, excel_filename)
                    if os.path.exists(excel_path):
                        with open(excel_path, 'rb') as f:
                            file_data = f.read()
                        os.remove(excel_path)
                        if os.path.exists(output_path):
                            os.remove(output_path)
                            
                        return attach_audit_headers(FileResponse(io.BytesIO(file_data), as_attachment=True, filename=original_filename.replace('.pdf', '.xlsx')))
                        
                if os.path.exists(output_path):
                    with open(output_path, 'rb') as f:
                        file_data = f.read()
                    os.remove(output_path)
                    excel_path = output_path.replace('.csv', '.xlsx')
                    if os.path.exists(excel_path):
                        os.remove(excel_path)
                        
                    return attach_audit_headers(FileResponse(io.BytesIO(file_data), as_attachment=True, filename=original_filename.replace('.pdf', '.csv')))
                    
                log.error_message = "Output file was not found after successful conversion."
                log.save()
                is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Conversion succeeded but output file was not found.'}, status=500)
                messages.error(request, 'Conversion succeeded but output file was not found.')
                return redirect('/')
            else:
                log.duration_seconds = round(time.time() - start_time, 2)
                log.error_message = "Bank logic returned false (Bank not supported or invalid statement)."
                log.save()
                is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Conversion failed or bank not supported. Please make sure it is a valid statement.'}, status=400)
                messages.error(request, 'Conversion failed or bank not supported. Please make sure it is a valid statement.')
                return redirect('/')
        except Exception as e:
            log.duration_seconds = round(time.time() - start_time, 2)
            log.error_message = str(e)
            log.save()
            try:
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
            except Exception:
                pass
            is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
            if is_ajax:
                return JsonResponse({'success': False, 'error': f'Error occurred: {str(e)}'}, status=500)
            messages.error(request, f'Error occurred: {str(e)}')
            return redirect('/')
            
    return render(request, 'converter/index.html', {'ocr_available': ocr_supported})
