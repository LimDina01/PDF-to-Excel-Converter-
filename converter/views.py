import os
import io
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import FileResponse, JsonResponse
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from convert_statement import extract_bank_statement
from .models import ConversionLog
import os

@login_required
def index(request):
    if request.method == 'POST' and request.FILES.get('pdf_file'):
        pdf_file = request.FILES['pdf_file']
        bank = request.POST.get('bank', 'Auto-Detect')
        include_summary = request.POST.get('include_summary') in ['on', 'true', '1']
        export_format = request.POST.get('export_format', 'csv')
        original_filename = pdf_file.name
        
        # Initialize the log entry
        log = ConversionLog.objects.create(
            filename=original_filename,
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
            success = extract_bank_statement(pdf_path, output_path, bank=bank, include_summary=include_summary)
            
            # Delete the original PDF file immediately for privacy
            try:
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
            except Exception:
                pass
                
            if success:
                log.is_successful = True
                log.save()
                
                if export_format == 'excel':
                    excel_filename = os.path.splitext(filename)[0] + "_converted.xlsx"
                    excel_path = os.path.join(settings.MEDIA_ROOT, excel_filename)
                    if os.path.exists(excel_path):
                        # Read to memory and delete physical files
                        with open(excel_path, 'rb') as f:
                            file_data = f.read()
                        os.remove(excel_path)
                        if os.path.exists(output_path):
                            os.remove(output_path) # Clean up the CSV it generated too
                            
                        return FileResponse(io.BytesIO(file_data), as_attachment=True, filename=original_filename.replace('.pdf', '.xlsx'))
                        
                if os.path.exists(output_path):
                    # Read to memory and delete physical files
                    with open(output_path, 'rb') as f:
                        file_data = f.read()
                    os.remove(output_path)
                    excel_path = output_path.replace('.csv', '.xlsx')
                    if os.path.exists(excel_path):
                        os.remove(excel_path) # Clean up the Excel it generated too
                        
                    # Return the CSV file as a download
                    return FileResponse(io.BytesIO(file_data), as_attachment=True, filename=original_filename.replace('.pdf', '.csv'))
                    
                log.error_message = "Output file was not found after successful conversion."
                log.save()
                is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Conversion succeeded but output file was not found.'}, status=500)
                messages.error(request, 'Conversion succeeded but output file was not found.')
                return redirect('/')
            else:
                log.error_message = "Bank logic returned false (Bank not supported or invalid statement)."
                log.save()
                is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Conversion failed or bank not supported. Please make sure it is a valid statement.'}, status=400)
                messages.error(request, 'Conversion failed or bank not supported. Please make sure it is a valid statement.')
                return redirect('/')
        except Exception as e:
            log.error_message = str(e)
            log.save()
            # Ensure PDF is deleted even on error
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
            
    return render(request, 'converter/index.html')
